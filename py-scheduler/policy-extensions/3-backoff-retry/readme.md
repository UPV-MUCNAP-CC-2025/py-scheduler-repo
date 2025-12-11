# Backoff and retries

This implementation backoff and retry strategy for pod scheduling.

## Usage.

### Requirements.

This guide assumes you have a valid docker image to schedule as follows `my-py-scheduler:latest`.

It also assumes you need a kubernetes dependency installed

````
pip3 install kubernetes==29.0.0
````

### 1. Create the cluster:
`````
kind create cluster --name sched-lab 
Creating cluster "sched-lab" ...
 ✓ Ensuring node image (kindest/node:v1.34.0) 🖼
 ✓ Preparing nodes 📦  
 ✓ Writing configuration 📜 
 ✓ Starting control-plane 🕹️ 
 ✓ Installing CNI 🔌 
 ✓ Installing StorageClass 💾 
Set kubectl context to "kind-sched-lab"
You can now use your cluster with:

kubectl cluster-info --context kind-sched-lab

Not sure what to do next? 😅  Check out https://kind.sigs.k8s.io/docs/user/quick-start/
`````

### 2. Load the docker image in the nodes.

````
kind load docker-image my-py-scheduler:latest --name sched-lab
Image: "my-py-scheduler:latest" with ID "sha256:3af49b0521e7ed1f6b80d72425c47d45e1fb9695a4ca02b0762236c2c3e106a4" not yet present on node "sched-lab-control-plane", loading...
````

### 3. Deploy pods.
````
kubectl apply -f test-pod.yaml                                
pod/test-pod-backoff-and-retries created
````
Because we are using the watch-scheduler, they will be pending until you run the scheduler.

````
kubectl  get pods -o wide                                     
NAME                           READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES
test-pod-backoff-and-retries   0/1     Pending   0          4s    <none>   <none>   <none>           <n
````

### 4. Run the scheduler.

````
 python3 watch-scheduler.py --scheduler-name my-scheduler --kubeconfig ~/.kube/config

[watch-student] scheduler starting… name=my-scheduler
[watch-scheduler] event=ADDED pod=default/test-pod-backoff-and-retries
[watch-scheduler] transient error in bind attempt=1: status=500 reason=Simulated internal error
[watch-scheduler] transient error in bind attempt=2: status=500 reason=Simulated internal error
[watch-scheduler] bind OK default/test-pod-backoff-and-retries -> sched-lab-control-plane (attempt=3)
````

### 4. Deploy pods (2)

````
kubectl  get pods -o wide
NAME                           READY   STATUS              RESTARTS   AGE   IP       NODE                      NOMINATED NODE   READINESS GATES
test-pod-backoff-and-retries   0/1     ContainerCreating   0          15s   <none>   sched-lab-control-plane   <none>           <none>
````

````
kubectl  get pods -o wide
NAME                           READY   STATUS              RESTARTS   AGE   IP       NODE                      NOMINATED NODE   READINESS GATES
test-pod-backoff-and-retries   0/1     ContainerCreating   0          16s   <none>   sched-lab-control-
````