scoutrace-flowsimulation
========================

Simulation tool for linear scout races modelled as directed graphs with node capacity

Requires Python 3. Further requirements are listed in requirements.txt and can be installed with `pip install -r requirements.txt`

Select a route definition when starting the simulation:

```sh
python flowsimulation.py --route rute2026.py
```

The route file defaults to `rute2026.py`. Relative route paths are resolved from the project directory; absolute paths are also accepted. Route files define a `course` mapping and may expose activities as either `Act` or `Activities`.

## Methodology

Each route is a mapping for `V`, `S`, and `OB`. A route is represented as alternating activity and distance-in-kilometres values, ending with an activity. The displayed route distance is the sum of its numeric distance entries.

Teams start in batches at the configured group start times. In the current configuration, `V`, `S`, and `OB` start at 08:00, 10:00, and 11:00. Three, four, and four teams respectively start together, with each subsequent batch 15 minutes later. Each team receives one walking speed per simulation run, sampled from its group’s normal distribution. The walking time for a route segment is:

```text
walking time (minutes) = distance (kilometres) / speed (kilometres per hour) * 60
```

An activity is a SimPy resource with a fixed concurrent-team capacity. Teams wait until a resource slot is available, then occupy it for a duration sampled uniformly between the activity’s configured minimum and maximum. On completing a timed activity, the resource is released and its service-end time is recorded. Activities with `None` duration, such as the finish marker, take no service time. Queue waits begin on arrival at the resource and end when a slot is granted.

Each run creates a new simulation environment and resources. Python’s pseudorandom generator is initialized with seed `1`; subsequent runs continue the same random stream, making repeated runs reproducible under the same code and runtime. Simulations stop at 30 hours after midnight (06:00 the following day). Output times are not wrapped at 24 hours, so a displayed hour above 24 is on the following day. A team that has not finished by the horizon is counted as incomplete; its finish time is excluded from completion-time percentiles. Waiting-time summaries still include the work completed in incomplete runs.

For each activity, the activity summary reports the 5th percentile of the first service-start time and the 95th percentile of the last service-end time, combining the per-run values from all team types. The Gantt chart shows the 5th/95th, 10th/90th, 25th/75th, and median start/end ranges separately for each team type; team types that do not visit an activity are omitted for that activity. The queue chart shows the distribution of each run's maximum number of teams waiting at each activity. Three-value time summaries are the 5th percentile, 95th percentile, and mean, in that order; displayed times are truncated to whole minutes.

These are model assumptions rather than measured guarantees: team speed is constant along a route within a run; speeds use unbounded normal distributions; activity durations are independent uniform draws; and each team uses one resource slot regardless of team size. In particular, the normal speed model theoretically permits non-positive samples, though the configured means and standard deviations make them very unlikely. Route distances, activity bounds, start schedules, and capacities should be adjusted to match the event being modeled.
