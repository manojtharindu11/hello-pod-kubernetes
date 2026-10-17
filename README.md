# Hello Pod Kubernetes Deployment

This directory contains a Kubernetes `Deployment` manifest for running the
`manojtharindu11/hello-pod` application.

## Files

- [`namespace.yml`](./namespace.yml) - Creates the `development` and
  `production` namespaces.
- [`app/`](./app/) - Contains the Flask application and its Docker files.
- [`.env.example`](./.env.example) - Shows example local environment values.
- [`.github/workflows/docker-publish.yml`](./.github/workflows/docker-publish.yml)
  - Builds and publishes the Docker image to Docker Hub.
- [`deployment.yml`](./deployment.yml) - Defines the Kubernetes Deployment and
  the Pods it should run in the `development` namespace.

## Environment variables

Copy [`.env.example`](./.env.example) to `.env` when running the container
locally with example Pod values:

```powershell
Copy-Item .env.example .env
docker run --env-file .env -p 3000:3000 manojtharindu11/hello-pod:1.0.0
```

Do not commit `.env`. It is ignored by Git. The Kubernetes Deployment does not
read this file; it supplies `POD_NAME`, `POD_NAMESPACE`, and `POD_IP`
automatically through the Downward API.

## Build and run the Flask application

The [`app/app.py`](./app/app.py) file defines a small Flask application that
listens on port `3000`. Its `/` endpoint returns JSON containing a greeting and
the Pod values supplied by Kubernetes:

- `POD_NAME`
- `POD_NAMESPACE`
- `POD_IP`

The [`app/Dockerfile`](./app/Dockerfile) installs the dependencies from
[`app/requirements.txt`](./app/requirements.txt), copies the application, and
starts Flask on `0.0.0.0:3000`. The application must bind to `0.0.0.0` so it
can receive traffic from outside the container.

Build the image from the project directory:

```powershell
docker build -t manojtharindu11/hello-pod:1.0.0 .\app
```

Push it to Docker Hub if the Kubernetes cluster needs to pull it:

```powershell
docker push manojtharindu11/hello-pod:1.0.0
```

The image tag above matches the image configured in `deployment.yml`.

## Publish with GitHub Actions

The `docker-publish` workflow runs on pushes to `main` and can also be started
manually. It builds the Docker image using [`app/Dockerfile`](./app/Dockerfile)
and publishes it to Docker Hub as:

- `1.0.0` on the default branch
- `latest` on the default branch
- A commit-SHA tag for every workflow run

Add these repository secrets in GitHub before running the workflow:

- `DOCKERHUB_USERNAME` - Your Docker Hub username.
- `DOCKERHUB_TOKEN` - A Docker Hub access token, not your account password.

The Deployment currently references
`manojtharindu11/hello-pod:1.0.0`. Set `DOCKERHUB_USERNAME` to
`manojtharindu11` or update the image name in `deployment.yml` to match your
Docker Hub repository.

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
2. Configure `kubectl` to use a running Kubernetes cluster.

The Docker image must also be publicly accessible, or the cluster must have
credentials to pull it.

## Create the namespaces

Apply the namespace manifest before applying the Deployment:

```powershell
kubectl apply -f namespace.yml
```

This creates both `development` and `production` if they do not already
exist. Namespace creation is safe to repeat because `kubectl apply` updates
existing resources instead of creating duplicates.

## Deploy the application

Apply the manifest with:

```powershell
kubectl apply -f deployment.yml
```

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

## Remove the Deployment

To remove the Deployment and the Pods it manages:

```powershell
kubectl delete -f deployment.yml
```

To remove both namespaces and all resources inside them:

```powershell
kubectl delete -f namespace.yml
```

Deleting a namespace is destructive: Kubernetes also deletes the resources
contained in that namespace.
