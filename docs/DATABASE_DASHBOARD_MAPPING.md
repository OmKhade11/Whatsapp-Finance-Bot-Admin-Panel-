# Live Supabase to Admin Dashboard Mapping

Inspected read-only against the configured Supabase project on 2026-10-30.

## Verified operational tables

| Dashboard area | Supabase source | Status |
|---|---|---|
| Users | `public.users` | Connected |
| Admin roles | `public.admin_roles` | Table exists; one role row |
| Admin users | `public.admin_users` | Table exists; currently zero rows |
| Subscription plans | `public.subscription_plans` | Connected; 3 active plans |
| User subscriptions | `public.user_subscriptions` | Connected |
| Payments | `public.payments` | Connected; currently no rows |
| Income | `public.income_records` | Available |
| Expenses | `public.expense_records` | Available |
| Budgets | `public.budgets`, `public.budget_items` | Available |
| Notifications | `public.user_notifications`, `public.notification_templates` | Connected; currently no rows |
| Business profiles | `public.business_profiles` | Connected; currently no rows |
| SWOT | `public.swot_analyses` | Connected; currently no rows |
| Capital | `public.capital_allocations` | Available |
| Pricing | `public.pricing_analyses` | Available |
| AI usage | `public.ai_conversations`, `public.ai_messages` | Connected; currently no rows |
| WhatsApp/finance messages | `public.finance_messages` | 117 rows; not yet used for AI metrics |

## Not yet represented in the live schema

- `audit_logs`
- Privacy policies and versions
- Consent/acknowledgement records
- Data subject requests
- Privacy incidents
- Data retention policies
- Third-party processor register

## Security findings

- RLS is enabled on the public application tables.
- Only `finance_messages` currently has visible policies in the inspected schema.
- `admin_users` has no rows, so no administrator is currently provisioned through the ERD model.
- The application still uses a development `X-Admin` header adapter; it must be replaced with verified Supabase Auth plus a server-side role check before production.

No schema changes were made during inspection.
