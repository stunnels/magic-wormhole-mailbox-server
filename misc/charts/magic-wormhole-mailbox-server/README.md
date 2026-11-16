# wormhole-mailbox Helm chart

Deploys the Magic-Wormhole mailbox server as a horizontally scalable
StatefulSet. The chart bundles
[Bitnami PostgreSQL](https://github.com/bitnami/charts/tree/main/bitnami/postgresql)
for shared channel, usage, and address-id state, and gives every pod its own
PersistentVolume so the server's persistent `replica.id` survives restarts.

## Install

```shell
helm dependency build misc/charts/wormhole-mailbox
helm install my-relay misc/charts/wormhole-mailbox \
  --namespace wormhole --create-namespace
```

The default values run three replicas behind an HPA, a PodDisruptionBudget,
preferred pod anti-affinity, and an Ingress for `mailbox.example.com`. Change
`ingress.hosts`, `ingress.className`, and either `image.repository` or
`image.tag` before installing for real.

To use a Gateway API Gateway instead of an Ingress, set `ingress.enabled=false`
and configure `gatewayAPI`; see [Gateway API](#gateway-api).

## Image

The chart does not publish an image. Build one from the repository root and
push it to your registry:

```shell
docker build -f misc/Dockerfile -t registry.example.com/magic-wormhole-mailbox:0.8.0 .
docker push registry.example.com/magic-wormhole-mailbox:0.8.0
```

Then set:

```yaml
image:
  repository: registry.example.com/magic-wormhole-mailbox
  tag: "0.8.0"
```

The image's entrypoint is `twist wormhole-mailbox`. The chart mounts a small
wrapper at `/scripts/entrypoint.sh` that assembles the database URLs at
container start-up and exports them as `WORMHOLE_CHANNEL_DB`,
`WORMHOLE_USAGE_DB`, and `WORMHOLE_ADDRID_DB`. The server reads those
environment variables, so credentials never appear in the pod spec or in the
process argument list.

The credentials do exist in the container's environment, which is readable by
node-level operators (for example through `/proc/<pid>/environ`). That trade-off
is deliberate: it keeps the password out of `ps` output and exec-audit logs.

## Replica identity

Each StatefulSet pod mounts its own PVC at `/data` and passes
`--replica-id-file=/data/replica.id`. The server creates that file atomically
the first time it starts. The same id is used for the usage database (the
per-replica `current` row and event attribution) and the channel database
(connection ownership and heartbeat).

A few consequences:

- Do not run two pods against the same `/data` volume.
- Scaling down leaves the PVCs behind, so a pod that later comes back on the
  same ordinal keeps its original identity. Delete the PVCs manually when you
  want to discard that identity.
- `persistence.enabled=false` falls back to `emptyDir`; the replica id is then
  regenerated on every restart. That is only suitable for single-replica
  experiments.

## Database layout

The mailbox server stores channel, usage, and address-id state in **separate
databases** because they reuse table names (`nameplates`, `mailboxes`, ...).
The bundled PostgreSQL subchart creates:

| Setting | Default database | Role |
| --- | --- | --- |
| `database.channelName` | `wormhole` | channel state |
| `database.usageName` | `wormhole_usage` | usage accounting |
| `database.addridName` | `wormhole_addrid` | address-id tracking |

The extra databases are created by
`postgresql.primary.initdb.scripts`. If you change
`postgresql.auth.username` or `postgresql.auth.database`, update that script and
the matching `database.*Name` values together.

Disable `config.usageDb.enabled` or `config.addridDb.enabled` to omit those
databases and flags.

### External database

```yaml
postgresql:
  enabled: false

database:
  host: postgres.example.internal
  port: 5432
  username: wormhole
  channelName: wormhole
  usageName: wormhole_usage
  addridName: wormhole_addrid
  sslmode: require
  existingSecret: wormhole-mailbox-db
  existingSecretKey: password
```

Create the three databases yourself, owned by `database.username`. The
existing Secret must contain the password under `existingSecretKey`. If you
prefer the chart to create the Secret, set `database.password` instead of
`database.existingSecret` (not recommended for production).

`database.scheme` defaults to `postgresql+psycopg`. For MariaDB/MySQL set it to
`mysql+pymysql`; the image ships both drivers.

## Pub/sub

The server needs cross-process fan-out for live WebSocket updates:

- PostgreSQL (`config.pubsub: auto`, the default) uses `LISTEN`/`NOTIFY`, so no
  extra service is needed.
- `config.pubsub: redis://redis:6379/0` or `kafka://kafka:9092` works with any
  channel database.
- SQLite and MySQL without Redis/Kafka are single-process only.

Only one replica should perform a given mailbox operation; the transport is
selected per replica, so keep `config.pubsub` identical across the StatefulSet.

## Gateway API

`gatewayAPI.enabled` renders an `HTTPRoute` that attaches to one or more
existing Gateways. It requires the Gateway API CRDs and a Gateway controller;
the chart does not install either. TLS is terminated by the Gateway listener,
so there is no certificate configuration here.

```yaml
ingress:
  enabled: false

gatewayAPI:
  enabled: true
  parentRefs:
    - name: nginx-gateway
      namespace: nginx-gateway
      sectionName: https
  hostnames:
    - mailbox.example.com
```

`parentRefs` and `hostnames` are passed through to the `HTTPRoute`. Each
hostname must be served by a listener on every parent Gateway. Keep
`ingress.enabled=false` unless you intentionally want both routes active.

Additional HTTPRoute options:

| Value | Default | Notes |
| --- | --- | --- |
| `gatewayAPI.path` | `/` | Path matched by the rule. |
| `gatewayAPI.pathType` | `PathPrefix` | `PathPrefix`, `Exact`, or `RegularExpression` (implementation-dependent). |
| `gatewayAPI.filters` | `[]` | HTTPRoute rule filters, such as `RequestHeaderModifier`. |
| `gatewayAPI.timeouts` | `{}` | Rule timeouts, e.g. `{request: 3600s, backendRequest: 3600s}`. |
| `gatewayAPI.annotations` / `labels` | `{}` | Applied to the `HTTPRoute`. |

WebSocket upgrades need the same long-lived connection settings as the Ingress
path. Configure an appropriate timeout on the Gateway or via
`gatewayAPI.timeouts` if your controller defaults to a short request timeout.

If `networkPolicy.enabled` is also true, add an ingress rule that allows traffic
from the Gateway's namespace (or its proxy pods) to port `4000`.

## Scaling

`autoscaling.enabled` creates an HPA over the StatefulSet. The server's live
connection rows are owned per replica, and each replica heartbeats every 30s;
replicas whose heartbeat is older than 150s are reaped together with their
connection rows. A replica never reaps itself, so a stalled event loop cannot
delete its own live sessions.

Set `autoscaling.enabled=false` to use a fixed `replicaCount`. Scaling a
StatefulSet with a `volumeClaimTemplates` section is supported, but every new
ordinal creates a new PVC.

## Probes and shutdown

Startup, readiness, and liveness probes are TCP checks against port `4000`.
`terminationGracePeriodSeconds` is 30 seconds, matching the server's graceful
shutdown path, which removes the local replica's connection rows.

## Optional resources

| Value | Default | Notes |
| --- | --- | --- |
| `ingress.enabled` | `true` | Includes WebSocket-friendly nginx annotations. |
| `gatewayAPI.enabled` | `false` | Renders an `HTTPRoute` attached to existing Gateway(s). |
| `podDisruptionBudget.enabled` | `true` | `minAvailable: 2`. |
| `autoscaling.enabled` | `true` | 3–10 replicas at 70% CPU. |
| `networkPolicy.enabled` | `false` | Allow DNS, the database port, and ingress on `4000`. |
| `serviceMonitor.enabled` | `false` | Requires a metrics endpoint; the server does not expose Prometheus metrics natively. |

## Upgrade notes

The server runs Alembic migrations at start-up and serializes them per database,
so multiple replicas can start against the same database safely. Pre-Alembic
SQLite databases are detected, backed up, and upgraded automatically.
