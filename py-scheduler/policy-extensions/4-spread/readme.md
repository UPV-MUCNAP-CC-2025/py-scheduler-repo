# Spread

This implementation spread placement strategy for pods.

## Usage.

### Requirements.

This guide assumes you have a valid docker image to schedule as follows `my-py-scheduler:latest`.

It also assumes you need a kubernetes dependency installed

````
pip3 install kubernetes==29.0.0
````

### 1. Create the cluster:
`````
kind create cluster --name sched-lab --config multinode.yaml
Creating cluster "sched-lab" ...
 ✓ Ensuring node image (kindest/node:v1.34.0) 🖼
 ✓ Preparing nodes 📦 📦 📦 📦  
 ✓ Writing configuration 📜 
 ✓ Starting control-plane 🕹️ 
 ✓ Installing CNI 🔌 
 ✓ Installing StorageClass 💾 
 ✓ Joining worker nodes 🚜 
Set kubectl context to "kind-sched-lab"
You can now use your cluster with:

kubectl cluster-info --context kind-sched-lab

Have a question, bug, or feature request? Let us know! https://kind.sigs.k8s.io/#community 
`````

### 2. Load the docker image in the nodes.

````
kind load docker-image my-py-scheduler:latest --name sched-lab
Image: "my-py-scheduler:latest" with ID "sha256:3af49b0521e7ed1f6b80d72425c47d45e1fb9695a4ca02b0762236c2c3e106a4" not yet present on node "sched-lab-control-plane", loading...
Image: "my-py-scheduler:latest" with ID "sha256:3af49b0521e7ed1f6b80d72425c47d45e1fb9695a4ca02b0762236c2c3e106a4" not yet present on node "sched-lab-worker3", loading...
Image: "my-py-scheduler:latest" with ID "sha256:3af49b0521e7ed1f6b80d72425c47d45e1fb9695a4ca02b0762236c2c3e106a4" not yet present on node "sched-lab-worker", loading...
Image: "my-py-scheduler:latest" with ID "sha256:3af49b0521e7ed1f6b80d72425c47d45e1fb9695a4ca02b0762236c2c3e106a4" not yet present on node "sched-lab-worker2", loading...
````

### 3. Deploy pods.
````
kubectl apply -f test-pods.yaml                               
pod/test-pod-1 created
pod/test-pod-2 created
pod/test-pod-3 created
pod/test-pod-4 created
````
Because we are using the watch-scheduler, they will be pending until you run the scheduler.

````
kubectl  get pods -o wide                                     
NAME         READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES
test-pod-1   0/1     Pending   0          6s    <none>   <none>   <none>           <none>
test-pod-2   0/1     Pending   0          6s    <none>   <none>   <none>           <none>
test-pod-3   0/1     Pending   0          6s    <none>   <none>   <none>           <none>
test-pod-4   0/1     Pending   0          6s    <none>   <none>   <none>           <none>
````

### 4. Run the scheduler.

````
python3 watch-scheduler.py --scheduler-name my-scheduler --kubeconfig ~/.kube/config

[watch-student] scheduler starting… name=my-scheduler
[watch-scheduler] event=ADDED pod=default/test-pod-1
[watch-scheduler] node sched-lab-control-plane score=9 (app=None)
[watch-scheduler] node sched-lab-worker score=2 (app=None)
[watch-scheduler] node sched-lab-worker2 score=2 (app=None)
[watch-scheduler] node sched-lab-worker3 score=2 (app=None)
[watch-scheduler] choosing node sched-lab-worker with score=2
[watch-scheduler] Bound default/test-pod-1 -> sched-lab-worker
[watch-scheduler] event=ADDED pod=default/test-pod-2
[watch-scheduler] node sched-lab-control-plane score=9 (app=None)
[watch-scheduler] node sched-lab-worker score=3 (app=None)
[watch-scheduler] node sched-lab-worker2 score=2 (app=None)
[watch-scheduler] node sched-lab-worker3 score=2 (app=None)
[watch-scheduler] choosing node sched-lab-worker2 with score=2
[watch-scheduler] Bound default/test-pod-2 -> sched-lab-worker2
[watch-scheduler] event=ADDED pod=default/test-pod-3
[watch-scheduler] node sched-lab-control-plane score=9 (app=None)
[watch-scheduler] node sched-lab-worker score=3 (app=None)
[watch-scheduler] node sched-lab-worker2 score=3 (app=None)
[watch-scheduler] node sched-lab-worker3 score=2 (app=None)
[watch-scheduler] choosing node sched-lab-worker3 with score=2
[watch-scheduler] Bound default/test-pod-3 -> sched-lab-worker3
[watch-scheduler] event=ADDED pod=default/test-pod-4
[watch-scheduler] node sched-lab-control-plane score=9 (app=None)
[watch-scheduler] node sched-lab-worker score=3 (app=None)
[watch-scheduler] node sched-lab-worker2 score=3 (app=None)
[watch-scheduler] node sched-lab-worker3 score=3 (app=None)
[watch-scheduler] choosing node sched-lab-worker with score=3
[watch-scheduler] Bound default/test-pod-4 -> sched-lab-worker
````

### 4. Deploy pods (2)

````
kubectl  get pods -o wide
NAME         READY   STATUS    RESTARTS   AGE   IP           NODE                NOMINATED NODE   READINESS GATES
test-pod-1   1/1     Running   0          9s    10.244.2.4   sched-lab-worker    <none>           <none>
test-pod-2   1/1     Running   0          9s    10.244.3.3   sched-lab-worker2   <none>           <none>
test-pod-3   1/1     Running   0          8s    10.244.1.3   sched-lab-worker3   <none>           <none>
test-pod-4   1/1     Running   0          8s    10.244.2.5   sched-lab-worker    <none>           <none>
````