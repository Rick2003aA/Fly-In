*This project has been created as part of the 42 curriculum by rtsubuku.*

# Fly-in

## Description

Fly-in is a pathfinding and simulation project in which a fleet of drones must be routed from a single `start_hub` to a single `end_hub` through a graph of connected zones.

The goal is not simply to find one shortest path. The real task is to move **all drones** to the end zone in the **fewest possible simulation turns** while respecting:

* zone movement costs,
* zone occupancy limits,
* connection capacity limits,
* simultaneous movement rules,
* and special behaviors such as `restricted` and `blocked` zones.

This project is implemented in **Python 3.10+**, must be **fully object-oriented**, and must pass **flake8** and **mypy**. Graph helper libraries such as `networkx` or `graphlib` are forbidden, so graph modeling, pathfinding, scheduling, and simulation must all be implemented manually.

---

## Project Goal

The objective is to route all drones from the start zone to the end zone in the smallest number of simulation turns.

A good solution must do more than compute a shortest path:

* distribute drones across multiple useful routes,
* decide when a drone should move and when it should wait,
* avoid conflicts and deadlocks,
* account for both zone and connection capacities,
* and handle multi-turn movements into `restricted` zones correctly.

The official evaluation is based primarily on the **total number of turns** used to deliver all drones.

---

## Simplified Rules Summary

This section is my own working summary of the subject. It is not meant to replace the official subject, but to make the operational rules easier to follow while implementing the project.

### 1. The map is a graph

The input file describes a graph:

* a **hub / zone** is a node,
* a **connection** is an edge.

There must be:

* exactly one `start_hub`,
* exactly one `end_hub`,
* zero or more regular `hub` entries,
* and zero or more `connection` entries.

### 2. Drones move in discrete turns

The simulation runs one turn at a time.

At each turn, a drone may:

* move to an adjacent zone,
* begin a multi-turn traversal toward a `restricted` zone,
* or stay in place.

Multiple drones may move during the same turn, as long as every movement remains valid.

### 3. Zone types define movement cost

Each zone has a type:

* `normal`: entering the zone costs **1 turn**,
* `restricted`: entering the zone costs **2 turns**,
* `priority`: entering the zone costs **1 turn**, but it should be preferred in pathfinding,
* `blocked`: the zone cannot be entered.

Important clarification:

* `priority` does **not** mean “must always be used”. It means the algorithm should prefer it when building routes.
* `restricted` does **not** simply mean “weight = 2”. The drone occupies the connection during transit and must arrive on the next turn.

### 4. Zone capacity and connection capacity both matter

By default:

* a zone can hold **1 drone**,
* a connection can be used by **1 drone at a time**.

Capacity can be increased with metadata:

* `max_drones=N` for zones,
* `max_link_capacity=N` for connections.

Special exceptions:

* the `start_hub` may initially contain all drones,
* the `end_hub` may receive multiple delivered drones.

### 5. Leaving a zone frees capacity during the same turn

Turn resolution is not purely “one drone after another”.

If a drone leaves a zone on a turn, that departure frees capacity for the same turn. This matters when two drones are effectively swapping usage across the graph or when a zone becomes available because another drone moved out.

### 6. Restricted moves are special

If a drone moves toward a `restricted` zone:

* the move takes **2 turns**,
* the drone occupies the connection during transit,
* the drone must reach the destination on the next turn,
* it may **not** wait extra turns on the connection.

That means a valid scheduler must check not only whether a drone can start the movement now, but also whether the destination will be valid on the next turn.

### 7. Output shows only moving drones

Each simulation turn is printed on one line.

That line contains only drones that moved during that turn:

* `D<ID>-<zone>` when the drone reaches a zone,
* `D<ID>-<connection>` when the drone is still in flight toward a restricted zone.

Drones that do not move are omitted from the line.

---

## Input Format

The map is provided as a text file.

Example:

```txt
nb_drones: 5
start_hub: hub 0 0 [color=green]
end_hub: goal 10 10 [color=yellow]
hub: roof1 3 4 [zone=restricted color=red]
hub: roof2 6 2 [zone=normal color=blue]
hub: corridorA 4 3 [zone=priority color=green max_drones=2]
hub: tunnelB 7 4 [zone=normal color=red]
hub: obstacleX 5 5 [zone=blocked color=gray]
connection: hub-roof1
connection: hub-corridorA
connection: roof1-roof2
connection: roof2-goal
connection: corridorA-tunnelB [max_link_capacity=2]
connection: tunnelB-goal
```

### File elements

#### `nb_drones`

```txt
nb_drones: <positive_integer>
```

Defines how many drones must be routed from start to end.

#### `start_hub`

```txt
start_hub: <name> <x> <y> [metadata]
```

Defines the unique starting zone.

#### `end_hub`

```txt
end_hub: <name> <x> <y> [metadata]
```

Defines the unique destination zone.

#### `hub`

```txt
hub: <name> <x> <y> [metadata]
```

Defines a regular intermediate zone.

#### `connection`

```txt
connection: <zone1>-<zone2> [metadata]
```

Defines a bidirectional connection between two previously declared zones.

#### Comments

```txt
# this is a comment
```

Comments begin with `#` and are ignored.

---

## Metadata

Metadata is written in brackets:

```txt
[color=green zone=priority max_drones=2]
```

Order does not matter.

### Zone metadata

* `zone=<type>`
* `color=<value>`
* `max_drones=<number>`

Defaults:

* `zone=normal`
* `color=none`
* `max_drones=1`

### Connection metadata

* `max_link_capacity=<number>`

Default:

* `max_link_capacity=1`

---

## Zone Types

### `normal`

Standard zone.

* movement cost: **1 turn**

### `blocked`

Inaccessible zone.

* drones must not enter it,
* drones must not pass through it,
* any path that uses it is invalid.

### `restricted`

Sensitive zone with multi-turn entry.

* movement cost to enter: **2 turns**,
* the drone occupies the connection while traveling,
* the drone must arrive next turn,
* the drone cannot wait on the connection.

### `priority`

Preferred zone.

* movement cost: **1 turn**,
* should be favored in pathfinding,
* but is **not mandatory**.

---

## Movement and Turn Mechanics

The simulation proceeds in discrete turns.

For each turn, every drone can do one of the following:

1. move to an adjacent zone,
2. begin a restricted traversal,
3. stay in place.

### Standard movement

A move into a `normal` or `priority` zone completes in one turn.

### Restricted movement

A move into a `restricted` zone completes in two turns:

* on turn `t`, the drone starts traversing the connection,
* on turn `t + 1`, the drone must enter the restricted zone.

The drone cannot remain on the connection longer than required.

### Waiting

A drone may stay in place if moving would violate a rule, create a conflict, or be strategically suboptimal.

### Simultaneous movement

Multiple drones may move during the same turn if all of the following remain valid:

* destination zone capacity,
* connection capacity,
* movement cost rules,
* no blocked entry,
* no impossible restricted arrival.

### Same-turn capacity release

If a drone leaves a zone, that departure frees capacity for the same turn. This means the simulation must evaluate the turn as a coordinated state transition, not as a naive one-by-one update.

---

## Occupancy Rules

### Zone occupancy

By default, a zone may contain at most **one drone** at a given simulation turn.

If a zone has:

```txt
[max_drones=N]
```

then up to `N` drones may occupy that zone simultaneously.

### Special cases

* **Start zone**: all drones begin here and may share it initially.
* **End zone**: multiple drones may arrive here and are considered delivered.

### Entry validity

A drone may not enter a zone if doing so would exceed the zone’s capacity after accounting for drones leaving that zone on the same turn.

### Connection occupancy

A connection may also have a capacity limit:

```txt
[max_link_capacity=N]
```

This limits how many drones can traverse that connection simultaneously.

This is especially important for restricted moves, because a restricted move occupies the connection during transit.

---

## Parser Constraints

The parser must reject invalid input clearly and stop with an informative error.

### Required parser rules

* The first line must be `nb_drones: <positive_integer>`.
* There must be exactly one `start_hub`.
* There must be exactly one `end_hub`.
* Zone names must be unique.
* Coordinates must be valid integers.
* Zone names cannot contain dashes (`-`) or spaces.
* Connections must reference only previously defined zones.
* Duplicate connections are forbidden.

  * `a-b` and `b-a` count as duplicates.
* Metadata blocks must be syntactically valid.
* Zone types must be one of:

  * `normal`
  * `blocked`
  * `restricted`
  * `priority`
* `max_drones` and `max_link_capacity` must be positive integers.
* Any parsing error should report both the line number and the reason.

### Why dashes are forbidden in zone names

Connections use this syntax:

```txt
connection: zone1-zone2
```

Because `-` is the separator, a zone name cannot itself contain `-`, otherwise parsing becomes ambiguous.

---

## Output Format

The simulation output is turn-based.

### Rules

* each line represents one simulation turn,
* only drones that moved during that turn appear on that line,
* entries are space-separated,
* delivered drones are no longer tracked,
* the simulation ends when all drones have reached the end zone.

### Output forms

#### Normal completed movement

```txt
D1-roof1
```

#### In-flight movement toward a restricted zone

```txt
D2-corridorA-tunnelB
```

In practice, the output form is defined as `D<ID>-<connection>` while the drone is still in flight toward a restricted zone.

### Example

```txt
D1-roof1 D2-corridorA
D1-roof2 D2-tunnelB
D1-goal D2-goal
```

---

## What Counts as a Valid Simulation

A simulation is valid only if all of the following are true:

* all drones eventually reach `end_hub`,
* all movement rules are respected,
* all zone movement costs are handled correctly,
* blocked zones are never entered,
* restricted traversals always complete correctly,
* no zone exceeds its capacity,
* no connection exceeds its capacity,
* no illegal collision or scheduling conflict occurs,
* output format is correct.

A solution that uses few turns but breaks even one of these rules is invalid.

---

## Scoring and Performance Targets

The main score is:

* **fewer total turns is better**.

Secondary metrics may also help compare two implementations with similar turn counts:

* drones moved per turn,
* average turns per drone,
* total weighted path cost,
* quality and usefulness of the visual representation.

### Subject benchmark targets

These benchmark targets are provided by the subject to help evaluate optimization quality.

#### Easy maps

* less than 10 turns overall target,
* reference examples include targets such as `<= 6` or `<= 8` turns.

#### Medium maps

* about `10–30` turns.

#### Hard maps

* less than `60` turns.

#### Challenger map

* optional,
* reference record: **41 turns**,
* does not affect the mandatory grade.

---

## Implementation Strategy

This section describes the intended architecture and algorithmic approach for this project.

### 1. Parsing layer

The parser reads the input file and transforms it into a strongly typed in-memory model.

Planned responsibilities:

* validate global structure,
* parse zones and connections,
* parse optional metadata,
* normalize defaults,
* reject invalid input early with meaningful errors.

### 2. Graph model

The map is represented as a custom graph structure.

Suggested core domain objects:

* `Zone`
* `Connection`
* `Graph`
* `Drone`
* `SimulationState`
* `Move` or `ScheduledMove`

This keeps the code object-oriented and separates parsing, routing, and simulation concerns.

### 3. Pathfinding strategy

A single static shortest path is not enough for this project.

The routing system must consider:

* weighted movement cost by destination zone type,
* route diversity,
* occupancy bottlenecks,
* link bottlenecks,
* and dynamic waiting.

A practical baseline strategy is:

1. compute candidate paths from start to end,
2. score them using weighted cost and route desirability,
3. assign or reassign drones turn by turn,
4. simulate using a scheduler that validates every planned move.

Depending on the final implementation, useful approaches may include:

* Dijkstra-style weighted shortest path,
* multi-path candidate generation,
* greedy scheduling with conflict checks,
* turn-by-turn rescheduling,
* caching path computations to reduce repeated work.

### 4. Scheduling layer

The scheduler is the true core of the project.

Its job is to decide, for each turn:

* which drones move,
* which drones wait,
* which connection slots are used,
* whether a restricted move can safely start,
* and whether the full turn remains conflict-free.

This is where throughput is won or lost.

### 5. Restricted movement handling

Restricted movement should be modeled explicitly instead of treating it as an ordinary edge weight.

A drone moving into a restricted zone should temporarily enter an **in-transit state** that stores at least:

* source zone,
* destination restricted zone,
* connection being occupied,
* remaining turns until arrival.

This makes the simulator easier to reason about and keeps the output logic clean.

### 6. Performance considerations

The subject explicitly asks evaluators to think about efficiency, complexity, path recalculation, and memory usage.

Optimization ideas:

* cache repeated shortest-path queries,
* precompute candidate paths when possible,
* avoid rebuilding the whole graph every turn,
* use compact occupancy tracking structures,
* separate immutable map data from mutable simulation state.

---

## Visual Representation

The subject requires visual feedback for the simulation.

My implementation is intended to provide at least one of the following:

* colored terminal output,
* graphical rendering of the network,
* or both.

### Why visualization matters

Visualization helps with:

* understanding congestion,
* debugging path allocation,
* verifying restricted traversal behavior,
* spotting capacity bottlenecks,
* and making peer evaluation easier.

### Planned visual feedback

A terminal-based view may include:

* colored zone names using metadata color,
* highlighted drone positions,
* visible distinction between idle drones and moving drones,
* special indication for drones in transit to restricted zones,
* and per-turn summaries.

If a GUI is added, it may additionally show:

* the graph layout using stored coordinates,
* animated or step-based drone movement,
* link usage,
* and current occupancy counts.

---

## Instructions

### Requirements

* Python 3.10+
* flake8
* mypy
* Make

### Expected Makefile targets

The subject requires the following rules:

* `install`
* `run`
* `debug`
* `clean`
* `lint`
* `lint-strict` (recommended optional target)

### Example usage

```bash
make install
make run
```

If the project is run directly:

```bash
python3 main.py maps/example.txt
```

If the simulation supports step mode or debug mode, that behavior should be documented here once finalized.

---

## Repository Structure

A possible project layout:

```txt
.
├── README.md
├── Makefile
├── main.py
├── src/
│   ├── parser/
│   ├── graph/
│   ├── simulation/
│   ├── pathfinding/
│   └── visualization/
├── maps/
└── tests/
```

The final repository may differ, but all required submission files must remain at the repository root as requested by the subject.

---

## Testing Approach

Tests are not explicitly graded, but they are strongly recommended.

I plan to test at least the following categories:

### Parser tests

* valid minimal map,
* invalid first line,
* duplicate zone names,
* invalid metadata,
* duplicate connections,
* undefined referenced zone,
* invalid zone type,
* non-positive capacity.

### Pathfinding tests

* simple linear graph,
* forked graph,
* blocked detour,
* priority preference,
* weighted restricted choice.

### Simulation tests

* same-turn zone release,
* connection capacity conflicts,
* restricted in-transit behavior,
* multiple drones arriving at end,
* deadlock-prone map behavior.

---

## Design Notes and Tradeoffs

This project sits at the intersection of:

* graph modeling,
* weighted routing,
* multi-agent scheduling,
* and discrete-event simulation.

The main design tradeoff is between:

* **optimality**: minimizing total turns as much as possible,
* and **simplicity / reliability**: keeping the simulation logic correct and explainable during peer evaluation.

My priority is to produce a solution that is:

1. correct,
2. understandable,
3. extensible,
4. then aggressively optimized.

That means I prefer:

* clear state modeling,
* explicit restricted-movement handling,
* deterministic scheduling where possible,
* and optimizations that do not make correctness harder to prove.

---

## AI Usage

AI was used as a support tool for:

* clarifying the official subject,
* checking ambiguous rule interpretations,
* refining README structure and wording,
* discussing architecture options,
* and brainstorming edge cases for parsing and simulation.

AI was **not** treated as an unquestioned source of truth. Every important rule was cross-checked against the official subject, and any generated explanation was reviewed critically before being kept.

---

## Resources

### Official project material

* 42 subject PDF for Fly-in

### General references

* Python documentation
* `typing` and `mypy` documentation
* `flake8` documentation
* graph theory and shortest-path references
* discrete simulation and scheduling references

### Useful topics to review

* graph representations with adjacency lists,
* Dijkstra’s algorithm,
* multi-agent path scheduling,
* conflict resolution in turn-based simulations,
* object-oriented domain modeling in Python.

---

## Final Notes

Evaluation maps may differ from the maps provided in the subject, so the implementation must remain general and robust.

During peer evaluation, I may be asked to:

* explain the architecture,
* justify algorithm choices,
* discuss complexity,
* modify a small part of the behavior,
* or add a minor feature quickly.

For that reason, this project is being designed not only to work, but also to remain easy to explain and adapt.