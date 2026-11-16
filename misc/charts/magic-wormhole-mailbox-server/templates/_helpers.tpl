{{/*
Common name helpers.
*/}}
{{- define "magic-wormhole-mailbox-server.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "magic-wormhole-mailbox-server.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{- define "magic-wormhole-mailbox-server.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "magic-wormhole-mailbox-server.selectorLabels" -}}
app.kubernetes.io/name: {{ include "magic-wormhole-mailbox-server.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "magic-wormhole-mailbox-server.labels" -}}
helm.sh/chart: {{ include "magic-wormhole-mailbox-server.chart" . }}
{{ include "magic-wormhole-mailbox-server.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "magic-wormhole-mailbox-server.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "magic-wormhole-mailbox-server.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{/*
Name of the bundled PostgreSQL Service/StatefulSet and its generated Secret.
Matches Bitnami's common.names.fullname for the postgresql subchart.
*/}}
{{- define "magic-wormhole-mailbox-server.postgresql.fullname" -}}
{{- if .Values.postgresql.fullnameOverride -}}
{{- .Values.postgresql.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- if contains "postgresql" .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-postgresql" .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Where the database password comes from.
*/}}
{{- define "magic-wormhole-mailbox-server.database.secretName" -}}
{{- if .Values.database.existingSecret -}}
{{- .Values.database.existingSecret -}}
{{- else if .Values.postgresql.enabled -}}
{{- if .Values.postgresql.auth.existingSecret -}}
{{- .Values.postgresql.auth.existingSecret -}}
{{- else -}}
{{- include "magic-wormhole-mailbox-server.postgresql.fullname" . -}}
{{- end -}}
{{- else -}}
{{- printf "%s-db" (include "magic-wormhole-mailbox-server.fullname" .) -}}
{{- end -}}
{{- end -}}

{{- define "magic-wormhole-mailbox-server.database.secretKey" -}}
{{- if .Values.database.existingSecret -}}
{{- .Values.database.existingSecretKey | default "password" -}}
{{- else if .Values.postgresql.enabled -}}
{{- .Values.postgresql.auth.secretKeys.userPasswordKey | default "password" -}}
{{- else -}}
password
{{- end -}}
{{- end -}}

{{- define "magic-wormhole-mailbox-server.database.host" -}}
{{- if .Values.database.host -}}
{{- .Values.database.host -}}
{{- else if .Values.postgresql.enabled -}}
{{- include "magic-wormhole-mailbox-server.postgresql.fullname" . -}}
{{- else -}}
{{- required "database.host is required when postgresql.enabled is false" .Values.database.host -}}
{{- end -}}
{{- end -}}

{{- define "magic-wormhole-mailbox-server.database.username" -}}
{{- if .Values.database.username -}}
{{- .Values.database.username -}}
{{- else if .Values.postgresql.enabled -}}
{{- .Values.postgresql.auth.username -}}
{{- else -}}
{{- required "database.username is required when postgresql.enabled is false" .Values.database.username -}}
{{- end -}}
{{- end -}}
