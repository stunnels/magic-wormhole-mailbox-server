{{/*
Common name helpers.
*/}}
{{- define "wormhole-mailbox.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "wormhole-mailbox.fullname" -}}
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

{{- define "wormhole-mailbox.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "wormhole-mailbox.selectorLabels" -}}
app.kubernetes.io/name: {{ include "wormhole-mailbox.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "wormhole-mailbox.labels" -}}
helm.sh/chart: {{ include "wormhole-mailbox.chart" . }}
{{ include "wormhole-mailbox.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "wormhole-mailbox.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "wormhole-mailbox.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{/*
Name of the bundled PostgreSQL Service/StatefulSet and its generated Secret.
Matches Bitnami's common.names.fullname for the postgresql subchart.
*/}}
{{- define "wormhole-mailbox.postgresql.fullname" -}}
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
{{- define "wormhole-mailbox.database.secretName" -}}
{{- if .Values.database.existingSecret -}}
{{- .Values.database.existingSecret -}}
{{- else if .Values.postgresql.enabled -}}
{{- if .Values.postgresql.auth.existingSecret -}}
{{- .Values.postgresql.auth.existingSecret -}}
{{- else -}}
{{- include "wormhole-mailbox.postgresql.fullname" . -}}
{{- end -}}
{{- else -}}
{{- printf "%s-db" (include "wormhole-mailbox.fullname" .) -}}
{{- end -}}
{{- end -}}

{{- define "wormhole-mailbox.database.secretKey" -}}
{{- if .Values.database.existingSecret -}}
{{- .Values.database.existingSecretKey | default "password" -}}
{{- else if .Values.postgresql.enabled -}}
{{- .Values.postgresql.auth.secretKeys.userPasswordKey | default "password" -}}
{{- else -}}
password
{{- end -}}
{{- end -}}

{{- define "wormhole-mailbox.database.host" -}}
{{- if .Values.database.host -}}
{{- .Values.database.host -}}
{{- else if .Values.postgresql.enabled -}}
{{- include "wormhole-mailbox.postgresql.fullname" . -}}
{{- else -}}
{{- required "database.host is required when postgresql.enabled is false" .Values.database.host -}}
{{- end -}}
{{- end -}}

{{- define "wormhole-mailbox.database.username" -}}
{{- if .Values.database.username -}}
{{- .Values.database.username -}}
{{- else if .Values.postgresql.enabled -}}
{{- .Values.postgresql.auth.username -}}
{{- else -}}
{{- required "database.username is required when postgresql.enabled is false" .Values.database.username -}}
{{- end -}}
{{- end -}}
