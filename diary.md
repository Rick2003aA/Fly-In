### Plan

#### Phase 1. Foundation: clean domain model

Goal:
- model the map and simulation state cleanly before adding turn logic
- keep static data and dynamic data separated
- make later parser, router, and simulator easier to build

Main work:
- `Zone`, `Connection`, `Graph` for static map data
- `Drone`, `DroneStatus`, `SimulationState` for dynamic turn-by-turn data
- helper methods for adjacency, occupancy, and drone lookup

Done when:
- graph structure can describe all zones and connections
- simulation state can describe where every drone is
- drone status meaning is clear and documented

#### Phase 2. State queries for one turn

Goal:
- answer questions about the current turn without mutating state yet

Main work:
- identify drones in restricted transit
- identify drones that must arrive this turn
- identify drones that are free to act
- inspect zone occupancy and connection occupancy easily

Done when:
- the code can answer “which drones must be resolved first this turn?”
- the code can answer “which drones are available to move now?”

#### Phase 3. One-turn simulation engine

Goal:
- simulate exactly one turn correctly

Main work:
- resolve forced restricted arrivals first
- compute free drones
- ask routing logic for candidate next actions
- resolve conflicts centrally
- apply accepted moves simultaneously

Conflict checks:
- blocked zones cannot be entered
- zone capacity must not be exceeded
- connection capacity must not be exceeded
- restricted-zone entry must stay valid across both turns
- simultaneous departures and arrivals must be handled correctly

Done when:
- one turn can be simulated deterministically
- occupancy is updated consistently
- moved drones for that turn can be listed

#### Phase 4. Routing strategy

Goal:
- choose useful paths for all drones, not only shortest path for one drone

Main work:
- basic pathfinding without forbidden libraries
- avoid blocked zones
- prefer priority zones when it helps
- support multiple useful routes
- avoid congestion and reduce total turns

Done when:
- router can suggest next moves for free drones
- drones are distributed in a way that improves total completion time

#### Phase 5. Full simulation loop

Goal:
- run turns until all drones are delivered

Main work:
- repeat one-turn simulation
- stop when all drones reach end hub
- collect output lines turn by turn
- keep delivered drones out of future movement logic

Done when:
- a full map can be simulated from start to finish
- total turns can be measured for comparison

#### Phase 6. Parser and input validation

Goal:
- load subject map files into domain objects safely

Main work:
- parse `nb_drones`
- parse `start_hub`, `end_hub`, `hub`, and `connection`
- parse metadata such as `zone`, `color`, `max_drones`, `max_link_capacity`
- ignore comments and invalid spacing robustly
- validate required structure

Validation checklist:
- exactly one start hub
- exactly one end hub
- all referenced zones exist
- blocked/restricted/priority values are valid
- capacities are valid positive numbers

Done when:
- input file can be turned into `Graph` + initial `SimulationState`

#### Phase 7. Output formatting

Goal:
- print output exactly in the subject format

Main work:
- one line per turn
- include only drones that moved
- print zone arrival as `D<ID>-<zone>`
- print restricted transit as `D<ID>-<connection>`

Done when:
- output lines match subject expectations for sample scenarios

#### Phase 8. Testing and refinement

Goal:
- verify correctness first, then improve performance and route quality

Manual test maps to prepare:
- one simple normal path
- one map with a restricted zone
- one map with a blocked zone
- one map with a priority route and a normal route
- one map with zone congestion
- one map with connection congestion
- one map that needs simultaneous move handling

Checks:
- every drone eventually arrives
- no invalid occupancy state appears
- no drone gets stuck in impossible restricted transit
- total turn count improves as routing gets smarter
- code passes `flake8` and `mypy`

#### Suggested build order

1. finish and clean domain/state models
2. add read-only simulation helpers
3. implement one-turn simulation
4. implement basic routing
5. implement parser
6. connect full simulation loop
7. polish output and tests

#### Current position

- Phase 1 is mostly done
- Phase 2 is the current focus
- next useful target: helper methods for restricted-transit drones and forced arrivals


### 2026/03/13
#### Step 1. Complete forced restricted arrivals

Any drone already in transit with remaining_travel_turns == 1 must try to arrive now.

If arrival cannot happen, that means your previous scheduling logic allowed an invalid restricted start. So ideally this should never fail.

goal of this phase:
- represent the map cleanly,
- represent drones cleanly,
- make later parsing and simulation easy,
- avoid putting rule logic everywhere.


src/
├── domain/
│   ├── enums.py
│   ├── zone.py
│   ├── connection.py
│   ├── drone.py
│   ├── graph.py
│   └── simulation_state.py






Step 2. Compute available departures

Determine which drones are free to act this turn:

drones in normal zones and not delivered

not drones already in transit

Step 3. Ask router for candidate next actions

For each free drone:

preferred next zone

fallback moves

wait if needed

Step 4. Resolve conflicts

Check:

zone capacity

connection capacity

simultaneous turn validity

This should be centralized, probably in scheduler.py.

Step 5. Apply moves simultaneously

Do not mutate one drone at a time in a naive way.

Instead:

collect valid moves

apply departures

update connection occupancy

update arrivals

then generate output line

This is important because the subject treats movement turn-by-turn and only moved drones appear in that turn output.


### 2026/03/14
Static data: Graph. It shows what the world looks like: Zone, Connection, Graph 
→ made it yesterday

Dynamic data: simulation state: Drone, SimulationState
→ Yet to be done

What SimulationState shold probably store
1. current turn number
2. drones
3. zone occupancy
4. connection occupancy

### 2026/03/15
