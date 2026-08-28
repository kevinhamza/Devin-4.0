{{! Devin/assets/templates/discord_template.md (Using .md extension conceptually) }}
{{! Template for Discord messages using Markdown }}

**{{ title | default("Devin AI Notification") }}** :robot: {{! Bold Title with Emoji }}

{{ message_body | default("No specific message content provided.") }} {{! Main message body - can contain *italic*, __underline__, ~~strikethrough~~ }}

{{#if details}} {{! Conceptual conditional block }}
--- {{! Divider }}
**Details:**
{{#each details}} {{! Conceptual loop }}
- **{{@key | replace '_' ' ' | capitalize }}:** `{{this}}` {{! Bold key, Inline code value }}
{{/each}}
{{/if}}

{{#if code_snippet}} {{! Conceptual conditional block }}
**Code Snippet:**
```{{ code_language | default('text') }}
{{ code_snippet }}
``` {{! Multi-line code block }}
{{/if}}

{{#if status_update}} {{! Conceptual conditional block }}
*Status: {{ status_update }}* {{! Italic status }}
{{/if}}

{{#if warning_message}} {{! Conceptual conditional block }}
> **Warning:** {{ warning_message }} {{! Block quote for warnings }}
{{/if}}

{{#if action_url}} {{! Conceptual conditional block }}
[ {{ action_text | default("View Details") }} ]({{ action_url }}) {{! Link }}
{{/if}}

{{#if user_mention_id}} {{! Conceptual conditional block }}
FYI: <@{{ user_mention_id }}> {{! User Mention }}
{{/if}}

--- {{! Divider }}
*Triggered by: {{ triggered_by | default('System') }} | Timestamp: `{{ timestamp | default('N/A') }}`* {{! Footer/Context in italics }}
