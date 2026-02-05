# Experiment 2

The second experiment has the same setup as the first experiment but introduces more chaos. This is done by deleting several pods during the experiment.
The additional chaos will give the scheduler more opportunities to optimize the network graph. Ideally we observe even better values compared to the default K8 scheduler than in experiment 1.

- The experiment runs for **10min**
- worker-1 is an unreliable node. It reboots at minute {2,5,8}. The expected effect is, that the scheduler will avoid putting many pods on this node
- There are three Apps with 3 clients for a single server. All of them have 'high' communication requirements. They will exceed the links. We expect the scheduler to schedule clients in close proximity to their servers.
- **During the run, 3 pod-killing events will happen**
- No perfect schedule exists for this problem

## Walkthrough

### Preparation

Set up the experiment as depicted in the setup. Commit all applications to the cluster and let the scheduler bind them to nodes. Once they are scheduled, proceed.

### Execution

Start the clock. Reboot worker-1 at minutes 2,5 and 8. At minute 10, shut down the cluster.

Additionally kill pods as follows:

- Min 3: Kill the server and one client of App1
- Min 6: Kill the server and one client of App2
- Min 9: Kill client and server of App4

### Collect Logs

Collect all the logs:

- [ ] Application Logs
- [ ] Scheduler Logs
- [ ] Scheduler network graph

## Setup

![image](./setup.drawio.png)

- 8 nodes, 12 pods
- Pods of pairings: 3->1, 3->1, 2->1, 1->1, 1->1
