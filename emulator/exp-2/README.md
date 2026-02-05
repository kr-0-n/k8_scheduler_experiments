# Experiment 1

This first experiment is not meant to be realistic, but to showcase the strengths of our custom scheduler.

- The experiment runs for **10min**
- worker-1 is an unreliable node. It reboots at minute {2,5,8}. The expected effect is, that the scheduler will avoid putting many pods on this node
- There are three Apps with 3 clients for a single server. All of them have 'high' communication requirements. They will exceed the links. We expect the scheduler to schedule clients in close proximity to their servers.
- No perfect schedule exists for this problem

## Walkthrough

### Preparation

Set up the experiment as depicted in the setup. Commit all applications to the cluster and let the scheduler bind them to nodes. Once they are scheduled, proceed.

### Execution

Start the clock. Reboot worker-1 at minutes 2,5 and 8. At minute 10, shut down the cluster.

### Collect Logs

Collect all the logs:

- [ ] Application Logs
- [ ] Scheduler Logs
- [ ] Scheduler network graph

## Setup

![image](./setup.drawio.png)

- 8 nodes, 12 pods
- Pods of pairings: 3->1, 3->1, 2->1, 1->1, 1->1
