#!/usr/bin/env python3
"""
rgkit -- reference implementation of the Recovery Graph model.

Accompanies: "The Recovery Graph: A Formal Model for Queryable Operational
Continuity in Cloud-Native Systems".

Implements:
  * the Recovery Graph data model (nodes, typed recovery dependency edges,
    capability levels, evidence, policies);
  * well-formedness / consistency checks (C1-C6, acyclicity of the hard core);
  * recovery path closure, plan ordering, PERT-style earliest-completion
    schedule over the level-granular action graph (RTO_est);
  * blocking centrality, counterfactual removal, SCC-based cycle detection;
  * the six metrics: RPL, RCS, RRI, REC, density (+ recovery-only ratio),
    RDC;
  * the Online Boutique worked example used in Sec. 7.6 / Appendix of the
    paper, including the pathological circular-bootstrap variant.

Only dependency: networkx.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from typing import Optional

import networkx as nx

# ----------------------------------------------------------------------------
# Capability levels (Definition 2 in the paper): DOWN < P < F < O
# ----------------------------------------------------------------------------
DOWN, P, F, O = 0, 1, 2, 3
LEVEL_NAME = {DOWN: "DOWN", P: "P", F: "F", O: "O"}

# Edge kinds (Definition 3)
KINDS = ("order", "data", "verify", "capacity", "authz")

# Evidence classes (Table: evidence taxonomy)
EV_CLASSES = (
    "BI",   # backup integrity check
    "RR",   # restore / rebuild rehearsal
    "FD",   # failover drill
    "CE",   # chaos experiment
    "CA",   # configuration attestation (pinned, resolvable recovery assets)
    "CT",   # cross-service contract / validation test
    "CV",   # credential validity check
)


@dataclass
class Evidence:
    """Recovery evidence item (Definition 7)."""
    node: str
    cls: str
    age_days: float          # now - t(e)
    ttl_days: float          # validity horizon tau(e)
    verdict: str = "pass"    # pass | fail

    def freshness(self) -> float:
        """phi(e) = max(0, 1 - age/ttl) for passing evidence, else 0."""
        if self.verdict != "pass" or self.ttl_days <= 0:
            return 0.0
        return max(0.0, 1.0 - self.age_days / self.ttl_days)


@dataclass
class Node:
    """Recovery Graph vertex: a service or a recovery resource."""
    nid: str
    ntype: str = "svc"                 # svc | res
    tier: int = 3                      # 1 = most critical
    weight: float = 1.0
    seed: bool = False                 # recoverable from outside the graph
    req: tuple = ()                    # required evidence classes
    dur: dict = field(default_factory=lambda: {P: 5, F: 5, O: 5})  # minutes


@dataclass
class REdge:
    """Recovery dependency edge (Definition 3): src depends on dst."""
    src: str                 # dependent u
    dst: str                 # prerequisite v
    kind: str = "order"
    hard: bool = True
    stage: str = "start"     # start | complete
    plevel: int = F          # minimal level pi of dst required


class RecoveryGraph:
    def __init__(self, name: str = "G_R"):
        self.name = name
        self.nodes: dict[str, Node] = {}
        self.edges: list[REdge] = []
        self.evidence: list[Evidence] = []
        # runtime service graph D and its recovery classification
        self.runtime_edges: set[tuple] = set()
        self.classification: dict[tuple, str] = {}  # -> hard|soft|irrelevant

    # -- construction --------------------------------------------------------
    def add_node(self, node: Node):
        self.nodes[node.nid] = node

    def add_edge(self, *a, **kw):
        e = REdge(*a, **kw)
        assert e.kind in KINDS, e.kind
        self.edges.append(e)

    def add_evidence(self, *a, **kw):
        self.evidence.append(Evidence(*a, **kw))

    # -- derived graphs ------------------------------------------------------
    def hard_node_graph(self) -> nx.DiGraph:
        """Node-level enablement graph H: prerequisite -> dependent (hard)."""
        g = nx.DiGraph()
        g.add_nodes_from(self.nodes)
        for e in self.edges:
            if e.hard:
                g.add_edge(e.dst, e.src)
        return g

    def action_graph(self):
        """Level-granular action graph (Sec. 3.5): tasks (v, level)."""
        g = nx.DiGraph()
        for v, n in self.nodes.items():
            for lv in (P, F, O):
                g.add_node((v, lv), dur=float(n.dur.get(lv, 0)))
            g.add_edge((v, P), (v, F))
            g.add_edge((v, F), (v, O))
        for e in self.edges:
            if not e.hard:
                continue
            gate = P if e.stage == "start" else O
            g.add_edge((e.dst, e.plevel), (e.src, gate))
        return g

    # -- consistency / well-formedness --------------------------------------
    def check(self) -> dict:
        """Well-formedness W1-W4 and consistency C1-C6 (mechanisable part)."""
        out = {}
        ag = self.action_graph()
        out["W3_acyclic_hard_core"] = nx.is_directed_acyclic_graph(ag)
        if not out["W3_acyclic_hard_core"]:
            sccs = [sorted({v for v, _ in c})
                    for c in nx.strongly_connected_components(ag) if len(c) > 1]
            out["hard_cycles"] = sccs
        hn = self.hard_node_graph()
        srcs = {v for v in hn if hn.in_degree(v) == 0}
        out["C6_sources_are_seeds"] = sorted(
            v for v in srcs if not self.nodes[v].seed)
        out["C2_unclassified_runtime_edges"] = sorted(
            d for d in self.runtime_edges if d not in self.classification)
        out["C4_nodes_missing_fresh_evidence"] = sorted(
            v for v in self.nodes if not self.ready(v))
        return out

    # -- evidence, readiness, confidence -------------------------------------
    def best_phi(self, v: str, cls: str) -> float:
        return max((e.freshness() for e in self.evidence
                    if e.node == v and e.cls == cls), default=0.0)

    def e_loc(self, v: str) -> float:
        """Local evidence score (Definition 8)."""
        req = self.nodes[v].req
        if not req:
            return 1.0
        return sum(self.best_phi(v, c) for c in req) / len(req)

    def ready(self, v: str) -> bool:
        """Recovery readiness (Definition 8): every required class fresh."""
        return all(self.best_phi(v, c) > 0.0 for c in self.nodes[v].req)

    def confidence(self, soft_w: float = 0.5) -> dict[str, float]:
        """Recovery confidence C(v) (Definition 9), weakest-link over hard
        prerequisites, discounted by soft prerequisites."""
        hn = self.hard_node_graph()
        if not nx.is_directed_acyclic_graph(hn):
            raise ValueError("confidence undefined: hard core is cyclic")
        soft_pre: dict[str, list] = {v: [] for v in self.nodes}
        for e in self.edges:
            if not e.hard:
                soft_pre[e.src].append(e.dst)
        C: dict[str, float] = {}
        for v in nx.topological_sort(hn):        # prerequisites first
            hard_pre = list(hn.predecessors(v))
            c = self.e_loc(v)
            if hard_pre:
                c *= min(C[x] for x in hard_pre)
            for x in soft_pre[v]:
                if x in C:
                    c *= (1.0 - soft_w * (1.0 - C[x]))
            C[v] = c
        return C

    # -- paths, schedule, RTO ------------------------------------------------
    def closure(self, v: str) -> set[str]:
        """Recovery path node set: hard prerequisites of v, transitively."""
        return nx.ancestors(self.hard_node_graph(), v)

    def rpl_hops(self, v: str) -> int:
        """Recovery path length in hops: longest hard chain ending at v."""
        hn = self.hard_node_graph()
        depth: dict[str, int] = {}
        for u in nx.topological_sort(hn):
            preds = list(hn.predecessors(u))
            depth[u] = 0 if not preds else 1 + max(depth[p] for p in preds)
        return depth[v]

    def schedule(self):
        """Earliest start/finish per action under unbounded parallelism
        (Proposition 3): classic PERT longest-path on the action graph."""
        ag = self.action_graph()
        if not nx.is_directed_acyclic_graph(ag):
            raise ValueError("schedule infeasible: cyclic hard core")
        es, ef = {}, {}
        for a in nx.topological_sort(ag):
            es[a] = max((ef[p] for p in ag.predecessors(a)), default=0.0)
            ef[a] = es[a] + ag.nodes[a]["dur"]
        return es, ef

    def rto_est(self, v: str) -> float:
        _, ef = self.schedule()
        return ef[(v, O)]

    def critical_path(self, v: str) -> list:
        """Actions on the longest chain ending at (v, O)."""
        ag = self.action_graph()
        es, ef = self.schedule()
        path, cur = [], (v, O)
        while True:
            path.append(cur)
            preds = [p for p in ag.predecessors(cur)
                     if abs(ef[p] - es[cur]) < 1e-9]
            if not preds or es[cur] == 0.0 and not preds:
                break
            if not preds:
                break
            cur = max(preds, key=lambda p: ef[p])
            if es[path[-1]] == 0.0 and not list(ag.predecessors(cur)):
                path.append(cur)
                break
        return list(reversed(path))

    # -- bottlenecks & counterfactuals ---------------------------------------
    def blocking(self) -> dict[str, float]:
        """Blocking centrality B(x): total weight of nodes whose hard closure
        contains x (Sec. 4.3)."""
        hn = self.hard_node_graph()
        B = {}
        for x in self.nodes:
            desc = nx.descendants(hn, x)
            B[x] = sum(self.nodes[d].weight for d in desc)
        return B

    def counterfactual(self, x: str) -> set[str]:
        """Nodes rendered unrecoverable if x cannot be recovered (hard
        conjunctive semantics): exactly the hard descendants of x."""
        return nx.descendants(self.hard_node_graph(), x)

    # -- metrics -------------------------------------------------------------
    def metrics(self) -> dict:
        n = len(self.nodes)
        m = len(self.edges)
        C = self.confidence()
        w = {v: self.nodes[v].weight for v in self.nodes}
        wsum = sum(w.values())
        aligned = sum(1 for e in self.edges
                      if (e.src, e.dst) in self.runtime_edges
                      or (e.dst, e.src) in self.runtime_edges)
        classified = sum(1 for d in self.runtime_edges
                         if d in self.classification)
        rec_num = 0.0
        for v, node in self.nodes.items():
            if node.req:
                cov = sum(1 for c in node.req if self.best_phi(v, c) > 0)
                rec_num += w[v] * cov / len(node.req)
            else:
                rec_num += w[v]
        return {
            "|V|": n, "|E_R|": m, "|D|": len(self.runtime_edges),
            "density": m / (n * (n - 1)) if n > 1 else 0.0,
            "recovery_only_ratio": (m - aligned) / m if m else 0.0,
            "RDC": classified / len(self.runtime_edges)
                   if self.runtime_edges else 1.0,
            "RRI": sum(w[v] for v in self.nodes if self.ready(v)) / wsum,
            "REC": rec_num / wsum,
            "RCS_weighted": sum(w[v] * C[v] for v in C) / wsum,
            "RCS_min_tier1": min((C[v] for v in C
                                  if self.nodes[v].tier == 1), default=1.0),
        }


# ============================================================================
# Worked example: Online Boutique (public architecture) + platform resources
# ============================================================================
def online_boutique(pathological: bool = False) -> RecoveryGraph:
    g = RecoveryGraph("online-boutique")

    # --- services (tiers reflect the criticality policy of Sec. 7.6) --------
    svc = {
        "frontend":       (1, {P: 5,  F: 10, O: 15}),
        "checkout":       (1, {P: 5,  F: 10, O: 10}),
        "payment":        (1, {P: 5,  F: 10, O: 15}),
        "cart":           (1, {P: 5,  F: 5,  O: 10}),
        "redis-cart":     (1, {P: 10, F: 20, O: 10}),
        "productcatalog": (2, {P: 5,  F: 5,  O: 5}),
        "currency":       (2, {P: 5,  F: 5,  O: 5}),
        "shipping":       (2, {P: 5,  F: 5,  O: 5}),
        "email":          (3, {P: 5,  F: 5,  O: 5}),
        "recommendation": (3, {P: 5,  F: 5,  O: 5}),
        "ad":             (3, {P: 5,  F: 5,  O: 5}),
    }
    tier_w = {1: 3.0, 2: 2.0, 3: 1.0}
    for s, (tier, dur) in svc.items():
        req = ("CA", "RR", "BI") if s == "redis-cart" else ("CA", "RR")
        if s == "frontend":
            req = ("CA", "RR", "CT")
        g.add_node(Node(s, "svc", tier, tier_w[tier], False, req, dur))

    # --- recovery resources (largely invisible to runtime tracing) ----------
    res = {
        "k8s":        (False, ("CA", "RR"), {P: 25, F: 15, O: 10}),
        "obs":        (False, ("CA", "RR"), {P: 10, F: 10, O: 10}),
        "iac":        (True,  ("CA",),      {P: 5,  F: 5,  O: 5}),
        "registry":   (True,  ("CA",),      {P: 5,  F: 5,  O: 5}),
        "dns":        (True,  ("CA",),      {P: 5,  F: 5,  O: 10}),
        "secrets":    (True,  ("CA", "CV"), {P: 5,  F: 5,  O: 5}),
        "backup":     (True,  ("CA", "BI"), {P: 5,  F: 10, O: 15}),
        "paysandbox": (True,  ("CV", "CT"), {P: 5,  F: 5,  O: 20}),
    }
    for r, (seed, req, dur) in res.items():
        g.add_node(Node(r, "res", 2, 1.0, seed, req, dur))

    # --- runtime service graph D (from the public architecture) -------------
    D = [("frontend", x) for x in ("ad", "recommendation", "productcatalog",
                                   "cart", "checkout", "shipping", "currency")]
    D += [("checkout", x) for x in ("cart", "productcatalog", "currency",
                                    "shipping", "payment", "email")]
    D += [("recommendation", "productcatalog"), ("cart", "redis-cart")]
    g.runtime_edges = set(D)

    # --- recovery dependency edges E_R ---------------------------------------
    in_cluster = list(svc) + ["obs"]
    for s in in_cluster:                       # platform (order, recovery-only)
        g.add_edge(s, "k8s", "order", True, "start", F)
        g.add_edge(s, "registry", "order", True, "start", F)
    g.add_edge("k8s", "iac", "order", True, "start", F)
    for s in ("payment", "email", "cart", "frontend"):       # credentials
        g.add_edge(s, "secrets", "authz", True, "start", F)
    g.add_edge("redis-cart", "backup", "data", True, "start", F)
    g.add_edge("cart", "redis-cart", "data", True, "start", F)
    for x in ("payment", "currency", "productcatalog", "cart", "shipping"):
        g.add_edge("checkout", x, "order", True, "start", F)
    g.add_edge("checkout", "email", "order", False, "start", F)   # degraded-start
    g.add_edge("frontend", "productcatalog", "order", True, "start", F)
    g.add_edge("frontend", "cart", "order", True, "start", F)
    g.add_edge("frontend", "recommendation", "order", False, "start", F)
    g.add_edge("frontend", "ad", "order", False, "start", F)
    g.add_edge("frontend", "checkout", "verify", True, "complete", O)
    g.add_edge("frontend", "dns", "order", True, "complete", F)
    g.add_edge("frontend", "cart", "capacity", True, "complete", F)
    g.add_edge("recommendation", "productcatalog", "order", True, "start", F)
    g.add_edge("payment", "paysandbox", "verify", True, "complete", F)
    for s in in_cluster:                       # validation needs observability
        if s != "obs":
            g.add_edge(s, "obs", "verify", True, "complete", F)

    # --- recovery classification of runtime edges (C2 / RDC) -----------------
    cls = {d: "hard" for d in D}
    cls[("checkout", "email")] = "soft"
    cls[("frontend", "recommendation")] = "soft"
    cls[("frontend", "ad")] = "soft"
    # two runtime edges deliberately left unassessed in the audit scenario:
    del cls[("frontend", "shipping")], cls[("frontend", "currency")]
    g.classification = cls

    # --- evidence store as of the audit date ---------------------------------
    EV = [
        # node, class, age_days, ttl_days, verdict
        ("iac", "CA", 3, 90), ("registry", "CA", 3, 90), ("dns", "CA", 10, 90),
        ("secrets", "CA", 10, 90), ("secrets", "CV", 20, 30),
        ("backup", "CA", 10, 90), ("backup", "BI", 6, 30),
        ("paysandbox", "CV", 28, 30),          # nearly expired credentials
        # paysandbox CT missing entirely -> not ready
        ("k8s", "CA", 7, 90), ("k8s", "RR", 45, 180),
        ("obs", "CA", 7, 90), ("obs", "RR", 100, 180),
        ("redis-cart", "CA", 7, 90), ("redis-cart", "RR", 30, 90),
        ("redis-cart", "BI", 6, 30),
        ("cart", "CA", 7, 90), ("cart", "RR", 30, 90),
        ("checkout", "CA", 7, 90), ("checkout", "RR", 60, 90),
        ("payment", "CA", 7, 90), ("payment", "RR", 170, 90),  # stale rehearsal
        ("frontend", "CA", 7, 90), ("frontend", "RR", 30, 90),
        ("frontend", "CT", 12, 30),
        ("productcatalog", "CA", 7, 90), ("productcatalog", "RR", 40, 90),
        ("currency", "CA", 7, 90), ("currency", "RR", 40, 90),
        ("shipping", "CA", 7, 90), ("shipping", "RR", 40, 90),
        ("email", "CA", 7, 90),                 # RR missing
        ("recommendation", "CA", 7, 90), ("recommendation", "RR", 80, 90),
        ("ad", "CA", 7, 90), ("ad", "RR", 80, 90),
    ]
    for row in EV:
        g.add_evidence(*row)

    if pathological:
        # Circular bootstrap: cluster rebuild runbook lives in an in-cluster
        # wiki (the Facebook 2021 / CrowdStrike 2024 pattern).
        g.add_node(Node("wiki", "svc", 3, 1.0, False, ("CA",),
                        {P: 5, F: 5, O: 5}))
        g.add_edge("wiki", "k8s", "order", True, "start", F)
        g.add_edge("wiki", "registry", "order", True, "start", F)
        g.add_edge("k8s", "wiki", "order", True, "start", F)  # runbook needed
        g.add_evidence("wiki", "CA", 7, 90)
    return g


# ============================================================================
def fmt_minutes(m: float) -> str:
    return f"{int(m)//60}h{int(m)%60:02d}m" if m >= 60 else f"{int(m)}m"


def report(g: RecoveryGraph):
    print(f"== Recovery Graph report: {g.name} ==")
    chk = g.check()
    for k, v in chk.items():
        print(f"  {k}: {v}")
    if not chk["W3_acyclic_hard_core"]:
        print("  -> graph not recoverable as modelled; aborting analysis.")
        return
    M = g.metrics()
    print("-- metrics --")
    for k, v in M.items():
        print(f"  {k}: {v:.3f}" if isinstance(v, float) else f"  {k}: {v}")
    C = g.confidence()
    es, ef = g.schedule()
    print("-- per-node (tier-1 and resources) --")
    hdr = f"  {'node':<15}{'tier':<5}{'ready':<7}{'E_loc':<7}{'C':<7}" \
          f"{'RPL':<5}{'RTO_est':<9}"
    print(hdr)
    for v in sorted(g.nodes, key=lambda x: (g.nodes[x].tier, x)):
        n = g.nodes[v]
        print(f"  {v:<15}{n.tier:<5}{str(g.ready(v)):<7}"
              f"{g.e_loc(v):<7.2f}{C[v]:<7.2f}{g.rpl_hops(v):<5}"
              f"{fmt_minutes(g.rto_est(v)):<9}")
    print("-- blocking centrality (top 6, weighted) --")
    B = g.blocking()
    for x, b in sorted(B.items(), key=lambda kv: -kv[1])[:6]:
        print(f"  {x:<12} B={b:.0f}  blocks {len(g.counterfactual(x))} nodes")
    print("-- critical path to frontend O --")
    cp = g.critical_path("frontend")
    print("  " + " -> ".join(f"{v}:{LEVEL_NAME[l]}@{fmt_minutes(ef[(v,l)])}"
                             for v, l in cp))
    print("-- schedule (finish of F and O per node, minutes) --")
    for v in sorted(g.nodes, key=lambda v: ef[(v, O)]):
        print(f"  {v:<15} P@{ef[(v,P)]:>6.0f}  F@{ef[(v,F)]:>6.0f}"
              f"  O@{ef[(v,O)]:>6.0f}")


def self_test():
    g = online_boutique()
    assert g.check()["W3_acyclic_hard_core"]
    C1 = g.confidence()
    # monotonicity: adding fresh evidence never decreases confidence
    g.add_evidence("payment", "RR", 1, 90)
    C2 = g.confidence()
    assert all(C2[v] >= C1[v] - 1e-12 for v in C1), "monotonicity violated"
    # weakest link: C(v) <= C(x) for every hard prerequisite x
    hn = g.hard_node_graph()
    for v in g.nodes:
        for x in hn.predecessors(v):
            assert C2[v] <= C2[x] + 1e-12, (v, x)
    # RTO monotone under added dependency
    r1 = g.rto_est("frontend")
    g.add_edge("frontend", "obs", "order", True, "start", O)
    assert g.rto_est("frontend") >= r1 - 1e-9
    bad = online_boutique(pathological=True)
    assert not bad.check()["W3_acyclic_hard_core"], "cycle not detected"
    print("self-test OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pathological", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        self_test()
    else:
        report(online_boutique(pathological=a.pathological))
