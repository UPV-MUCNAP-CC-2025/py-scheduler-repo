# Taints and tolerations

This implementation filter nodes to do the pod placement. In this case the scheduler is responsible to choose a subset of valid nodes depending on metadata from pods and nodes. This is defined in the `multinode.yaml` file used by kind to create the cluster:

`````
- role: worker
  kubeadmConfigPatches:
  - |
    kind: JoinConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "env=prod"
        register-with-taints: "env=prod:NoSchedule"
`````

Pods definition is also conditioned by tolerations:

````
apiVersion: v1
kind: Pod
metadata:
  name: test-pod-non-prod-1
spec:
  schedulerName: my-scheduler
  tolerations:
  - key: "env"
    operator: "Equal"
    value: "non-prod"
    effect: "NoSchedule"
  containers:
  - name: pause
    image: registry.k8s.io/pause:3.9
````

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

Have a question, bug, or feature request? Let us know! https://kind.sigs.k8s.io/#community 🙂
`````

### 2. Load the docker image in the nodes.

````
kind load docker-image my-py-scheduler:latest --name sched-lab
Image: "my-py-scheduler:latest" with ID "sha256:3af49b0521e7ed1f6b80d72425c47d45e1fb9695a4ca02b0762236c2c3e106a4" not yet present on node "sched-lab-control-plane", loading...
Image: "my-py-scheduler:latest" with ID "sha256:3af49b0521e7ed1f6b80d72425c47d45e1fb9695a4ca02b0762236c2c3e106a4" not yet present on node "sched-lab-worker", loading...
Image: "my-py-scheduler:latest" with ID "sha256:3af49b0521e7ed1f6b80d72425c47d45e1fb9695a4ca02b0762236c2c3e106a4" not yet present on node "sched-lab-worker2", loading...
Image: "my-py-scheduler:latest" with ID "sha256:3af49b0521e7ed1f6b80d72425c47d45e1fb9695a4ca02b0762236c2c3e106a4" not yet present on node "sched-lab-worker3", loading...
````

### 3. Check node taints.

````
kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints
NAME                      TAINTS
sched-lab-control-plane   [map[effect:NoSchedule key:node-role.kubernetes.io/control-plane] map[effect:NoSchedule key:env value:control-plane]]
sched-lab-worker          [map[effect:NoSchedule key:env value:prod]]
sched-lab-worker2         [map[effect:NoSchedule key:env value:prod]]
sched-lab-worker3         [map[effect:NoSchedule key:env value:non-prod]]
````

### 4. Deploy pods.
````
kubectl apply -f test-pods.yaml                                            
pod/test-pod-prod-1 created
pod/test-pod-prod-2 created
pod/test-pod-prod-3 created
pod/test-pod-non-prod-1 created
pod/test-pod-non-prod-2 created
pod/test-pod-non-prod-3 created
````
Because we are using the watch-scheduler, they will be pending until you run the scheduler.

````
kubectl  get pods -o wide                                                  
NAME                  READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES
test-pod-non-prod-1   0/1     Pending   0          8s    <none>   <none>   <none>           <none>
test-pod-non-prod-2   0/1     Pending   0          8s    <none>   <none>   <none>           <none>
test-pod-non-prod-3   0/1     Pending   0          8s    <none>   <none>   <none>           <none>
test-pod-prod-1       0/1     Pending   0          8s    <none>   <none>   <none>           <none>
test-pod-prod-2       0/1     Pending   0          8s    <none>   <none>   <none>           <none>
test-pod-prod-3       0/1     Pending   0          8s    <none>   <none>   <none>           <none>
````

### 5. Run the scheduler.

````
python3 watch-scheduler.py --scheduler-name my-scheduler --kubeconfig ~/.kube/config

[watch-student] scheduler starting… name=my-scheduler
[watch-scheduler] event=ADDED pod=default/test-pod-non-prod-1
[watch-scheduler] Bound default/test-pod-non-prod-1 -> sched-lab-worker3
[watch-scheduler] event=ADDED pod=default/test-pod-non-prod-2
[watch-scheduler] Bound default/test-pod-non-prod-2 -> sched-lab-worker3
[watch-scheduler] event=ADDED pod=default/test-pod-non-prod-3
[watch-scheduler] Bound default/test-pod-non-prod-3 -> sched-lab-worker3
[watch-scheduler] event=ADDED pod=default/test-pod-prod-1
[watch-scheduler] Bound default/test-pod-prod-1 -> sched-lab-worker
[watch-scheduler] event=ADDED pod=default/test-pod-prod-2
[watch-scheduler] Bound default/test-pod-prod-2 -> sched-lab-worker2
[watch-scheduler] event=ADDED pod=default/test-pod-prod-3
[watch-scheduler] Bound default/test-pod-prod-3 -> sched-lab-worker
````

### 5. Deploy pods (2)

````
kubectl  get pods -o wide
NAME                  READY   STATUS              RESTARTS   AGE   IP       NODE                NOMINATED NODE   READINESS GATES
test-pod-non-prod-1   0/1     ContainerCreating   0          19s   <none>   sched-lab-worker3   <none>           <none>
test-pod-non-prod-2   0/1     ContainerCreating   0          19s   <none>   sched-lab-worker3   <none>           <none>
test-pod-non-prod-3   0/1     ContainerCreating   0          19s   <none>   sched-lab-worker3   <none>           <none>
test-pod-prod-1       0/1     ContainerCreating   0          19s   <none>   sched-lab-worker    <none>           <none>
test-pod-prod-2       0/1     ContainerCreating   0          19s   <none>   sched-lab-worker2   <none>           <none>
test-pod-prod-3       0/1     ContainerCreating   0          19s   <none>   sched-lab-worker    <none>           <none>

````

````
kubectl  get pods -o wide
NAME                  READY   STATUS    RESTARTS   AGE   IP           NODE                NOMINATED NODE   READINESS GATES
test-pod-non-prod-1   1/1     Running   0          21s   10.244.2.2   sched-lab-worker3   <none>           <none>
test-pod-non-prod-2   1/1     Running   0          21s   10.244.2.3   sched-lab-worker3   <none>           <none>
test-pod-non-prod-3   1/1     Running   0          21s   10.244.2.4   sched-lab-worker3   <none>           <none>
test-pod-prod-1       1/1     Running   0          21s   10.244.1.2   sched-lab-worker    <none>           <none>
test-pod-prod-2       1/1     Running   0          21s   10.244.3.2   sched-lab-worker2   <none>           <none>
test-pod-prod-3       1/1     Running   0          21s   10.244.1.3   sched-lab-worker    <none>           <none>
````