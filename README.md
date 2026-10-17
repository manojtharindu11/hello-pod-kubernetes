# Hello Pod Kubernetes Deployment

This directory contains a Kubernetes `Deployment` manifest for running the
`manojtharindu11/hello-pod` application.

## Files

- [`k8s/`](./k8s/) - Contains the Kubernetes manifests.
- [`k8s/namespace.yml`](./k8s/namespace.yml) - Creates the `development` and
  `production` namespaces.
- [`app/`](./app/) - Contains the Flask application and its Docker files.
- [`.env.example`](./.env.example) - Shows example local environment values.
- [`.github/workflows/docker-publish.yml`](./.github/workflows/docker-publish.yml)
  - Builds and publishes the Docker image to Docker Hub.
- [`k8s/busyBox.yml`](./k8s/busyBox.yml) - Creates a long-running BusyBox Pod for
  troubleshooting.
- [`k8s/deployment.yml`](./k8s/deployment.yml) - Defines the Kubernetes Deployment and
  the Pods it should run in the `development` namespace.
- [`k8s/service.yml`](./k8s/service.yml) - Exposes the Hello Pod Deployment through a
  Kubernetes Service.

## Environment variables

Copy [`.env.example`](./.env.example) to `.env` when running the container
locally with example Pod values:

```powershell
Copy-Item .env.example .env
docker run --env-file .env -p 3000:3000 manojtharindu11/hello-pod:latest
```

Do not commit `.env`. It is ignored by Git. In Kubernetes, the Deployment does
not use this local file; it supplies `POD_NAME`, `POD_NAMESPACE`, and `POD_IP`
automatically through the Downward API. Existing environment variables take
precedence over values loaded from `.env`.

## Build and run the Flask application

The [`app/app.py`](./app/app.py) file defines a small Flask application that
listens on port `3000`. It loads values from a local `.env` file using
`python-dotenv`, and its `/` endpoint returns JSON containing a greeting and
the Pod values:

- `POD_NAME`
- `POD_NAMESPACE`
- `POD_IP`

The [`app/Dockerfile`](./app/Dockerfile) installs the dependencies from
[`app/requirements.txt`](./app/requirements.txt), copies the application, and
starts Flask on `0.0.0.0:3000`. The application must bind to `0.0.0.0` so it
can receive traffic from outside the container.

Build the image from the project directory:

```powershell
docker build -t manojtharindu11/hello-pod:latest .\app
```

Push it to Docker Hub if the Kubernetes cluster needs to pull it:

```powershell
docker push manojtharindu11/hello-pod:latest
```

The image tag above matches the image configured in
[`k8s/deployment.yml`](./k8s/deployment.yml).

## Publish with GitHub Actions

The `docker-publish` workflow runs on pushes to `main` only when files under
[`app/`](./app/) change. It can also be started manually with
`workflow_dispatch`. It builds the Docker image using
[`app/Dockerfile`](./app/Dockerfile) and publishes it to Docker Hub as:

- `latest` on the default branch
- `1.0.0` on the default branch
- A commit-SHA tag for every workflow run

Add these repository secrets in GitHub before running the workflow:

- `DOCKERHUB_USERNAME` - Your Docker Hub username.
- `DOCKERHUB_TOKEN` - A Docker Hub access token, not your account password.

The Deployment currently references
`manojtharindu11/hello-pod:latest`. Set `DOCKERHUB_USERNAME` to
`manojtharindu11` or update the image name in
[`k8s/deployment.yml`](./k8s/deployment.yml) to match your Docker Hub
repository.

## Namespace manifest explained

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: development
```

- `apiVersion: v1` selects the core Kubernetes API.
- `kind: Namespace` declares a namespace resource.
- `metadata.name` sets the namespace name.

The manifest contains a second Namespace document with the name
`production`. The two documents are separated by `---`. The Deployment is
configured for `development`, so its Pods are created there and not in
`production`.

## Deployment manifest explained

### API version and resource type

```yaml
apiVersion: apps/v1
kind: Deployment
```

- `apiVersion` selects the Kubernetes API used for this resource.
- `kind` declares that the resource is a `Deployment`.

A Deployment manages replicated Pods and replaces Pods when they fail or when
the application is updated.

### Resource metadata

```yaml
metadata:
  name: hello-pod-deployment
  namespace: development
  labels:
    app: hello-pod
```

- `name` is the name of the Deployment: `hello-pod-deployment`.
- `namespace` places the Deployment in the `development` namespace. The
  namespace must already exist unless it is created separately.
- `labels` are key-value tags used to identify and organize Kubernetes
  resources.

### Deployment specification

```yaml
spec:
  replicas: 3
```

- `spec` contains the desired configuration for the Deployment.
- `replicas: 3` instructs Kubernetes to keep three identical Pods running.

### Pod selector

```yaml
  selector:
    matchLabels:
      app: hello-pod
```

The selector tells the Deployment which Pods it manages. It must match the
labels defined in the Pod template below.

### Pod template

```yaml
  template:
    metadata:
      labels:
        app: hello-pod
```

The template describes each Pod created by the Deployment.

- `template.metadata.labels` assigns the `app: hello-pod` label to every
  created Pod.
- This label matches `spec.selector.matchLabels`, allowing the Deployment to
  track its Pods.

### Container specification

```yaml
    spec:
      containers:
      - name: hello-pod-container
        image: manojtharindu11/hello-pod
```

- The nested `spec` describes the contents of each Pod.
- `containers` lists the containers that run in the Pod.
- `name` gives the container its name: `hello-pod-container`.
- `image` specifies the Docker image Kubernetes should run.

### Container port

```yaml
        ports:
        - containerPort: 3000
```

This documents that the application listens on port `3000` inside the
container. A Kubernetes `Service` is still required if the application needs
to be reached through a stable network endpoint.

### Resource requests and limits

```yaml
        resources:
          requests:
            memory: "64Mi"
            cpu: "250m"
          limits:
            memory: "128Mi"
            cpu: "500m"
```

- `requests` are the minimum CPU and memory resources Kubernetes reserves when
  scheduling each Pod.
- `limits` are the maximum CPU and memory resources the container can use.
- `m` means millicpu, so `250m` is one quarter of a CPU core.
- `Mi` means mebibytes of memory.

### Environment variables from Pod information

The following variables are populated automatically using Kubernetes' Downward
API:

```yaml
        env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
```

`POD_NAME` contains the name of the current Pod.

```yaml
        - name: POD_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
```

`POD_NAMESPACE` contains the namespace of the current Pod.

```yaml
        - name: POD_IP
          valueFrom:
            fieldRef:
              fieldPath: status.podIP
```

`POD_IP` contains the IP address assigned to the current Pod.

## Prerequisites

1. Install `kubectl`.
2. Install Minikube and a supported container runtime such as Docker.
3. Start Minikube before applying resources.

The Docker image must also be publicly accessible, or the cluster must have
credentials to pull it.

## Using Minikube

Start and inspect the local Kubernetes cluster:

```bash
minikube start
kubectl cluster-info
kubectl get nodes
minikube update-check
```

`minikube start` creates or starts the local cluster. `kubectl cluster-info`
checks that the Kubernetes control plane is reachable, while `kubectl get
nodes` shows the worker nodes available for scheduling. `minikube
update-check` reports whether a newer Minikube version is available.

Inspect cluster-wide resources:

```bash
kubectl get namespaces
kubectl get ns
kubectl get pods -A
kubectl get services -A
kubectl api-resources
```

`get namespaces` and its shorthand `get ns` list namespaces. The `-A` option
includes every namespace, rather than only the current namespace. `api-resources`
lists the resource types supported by the cluster.

Stop the cluster when it is not needed, or delete it when you want to remove
the cluster and its stored state:

```bash
minikube stop
minikube delete
```

## Apply and inspect Kubernetes resources

Create the project namespaces before deploying the application:

```bash
kubectl apply -f .\k8s\namespace.yml
kubectl get namespaces
```

Apply the Hello Pod Deployment and Service:

```bash
kubectl apply -f .\k8s\deployment.yml
kubectl apply -f .\k8s\service.yml
```

Inspect the Deployment and its Pods:

```bash
kubectl get deployments -n development
kubectl get pods -n development
kubectl get pods -n development -o wide
kubectl describe pod <pod-name> -n development
```

Use the actual Pod name returned by `kubectl get pods`; Pod names contain
generated suffixes and change when Pods are recreated. To remove one Pod and
allow the Deployment to create a replacement:

```bash
kubectl delete pod <pod-name> -n development
```

The Service selects Pods with the `app: hello-pod` label and forwards Service
port `80` to the container's port `3000`. Its `LoadBalancer` type requests an
external address from the cluster. On Minikube, use:

```powershell
minikube service demo-service -n development
kubectl get service -n development
```

The Service manifest names this Service `demo-service`.

## Verify the Deployment

Check the Deployment:

```powershell
kubectl get deployment hello-pod-deployment -n development
```

Check the Pods:

```powershell
kubectl get pods -n development -l app=hello-pod
```

Inspect the Deployment if a Pod does not start:

```powershell
kubectl describe deployment hello-pod-deployment -n development
```

View the application logs:

```powershell
kubectl logs -n development -l app=hello-pod
```

## Use the BusyBox troubleshooting Pod

Apply the debugging Deployment:

```powershell
kubectl apply -f .\k8s\busyBox.yml
```

Find its current Pod name:

```bash
kubectl get pods -n default -l app=busybox
```

The BusyBox container is kept alive by a loop so it can be used for interactive
troubleshooting. From Git Bash, use `sh` without the leading slash:

```bash
kubectl exec -it <busybox-pod-name> -n default -- sh
```

Git Bash can rewrite `/bin/sh` into a Windows path before `kubectl` receives
it. If the absolute path is required, disable that conversion:

```bash
MSYS_NO_PATHCONV=1 kubectl exec -it <busybox-pod-name> -n default -- /bin/sh
```

From inside BusyBox, test the Hello Pod directly using a Pod IP from
`kubectl get pods -n development -o wide`:

```sh
wget -O index.html http://<hello-pod-ip>:3000
cat index.html
exit
```

The response contains the greeting and the `POD_NAME`, `POD_NAMESPACE`, and
`POD_IP` values injected into the application container. Use `wget`, not
`winget`; `wget` is the BusyBox HTTP client, while `winget` is a Windows
package manager command.

Remove the troubleshooting Deployment when it is no longer needed:

```powershell
kubectl delete -f .\k8s\busyBox.yml
```

## Remove the Deployment

To remove the Deployment and the Pods it manages:

```powershell
kubectl delete -f .\k8s\deployment.yml
kubectl delete -f .\k8s\service.yml
```

To remove both namespaces and all resources inside them:

```powershell
kubectl delete -f .\k8s\namespace.yml
```

Deleting a namespace is destructive: Kubernetes also deletes the resources
contained in that namespace.

## View application logs

View logs from a specific Pod:

```bash
kubectl logs <pod-name> -n development
```

The Flask development server reports the address it is listening on and logs
each HTTP request. For production workloads, use a production WSGI server
instead of Flask's built-in development server.

## Kubernetes cluster components

### Control plane

- **Cloud Controller Manager** connects Kubernetes to a cloud provider and
  manages cloud-specific resources.
- **etcd** stores the cluster's configuration and current state. The
  kube-apiserver is the component that communicates directly with it.
- **kube-apiserver** exposes and validates the Kubernetes API and processes
  requests from `kubectl` and other cluster components.
- **kube-controller-manager** runs controllers that continuously reconcile the
  actual cluster state with the desired state.
- **kube-scheduler** assigns newly created, unscheduled Pods to suitable
  worker nodes.

### Worker nodes

- **Container runtime** pulls images and creates, starts, and manages
  containers.
- **kubelet** ensures the containers described by each Pod are running and
  communicates the node status to the API server.
- **kube-proxy** maintains network rules that allow communication between Pods
  and Services.
