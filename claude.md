Before starting any task:
	0.	Use TodoWrite to create a plan.md with the approach, then use AskUserQuestion to confirm I understand the goal and want to proceed
	0.	If anything is ambiguous, ask—don't assume
	0.	Explain technical decisions in plain language
When building:
	•	Simple > clever. I'm not a developer—if I can't understand what you built, I can't maintain it
	•	Test before declaring done
	•	Comment code explaining why, not just what
	•	One feature at a time, fully working, before moving on
When something breaks:
	•	Explain what went wrong in plain English
	•	Give me options with tradeoffs
	•	Don't spiral into complex fixes—sometimes starting fresh is better
About me:
	•	Financial analyst, basic tech knowledge
	•	I value working software over perfect architecture
	•	I trust you, but verify with me on decisions that are hard to reverse

Design direction:
* Modern, minimal aesthetic (reference: Linear, Notion, Stripe)
* Tailwind CSS + shadcn/ui for components
* Mobile-responsive, fast-loading
* Consistent spacing, typography, and color
* Subtle micro-interactions (hover states, transitions)
* Always include loading and error states

Technical defaults:
* Environment variables for secrets
* Clear file/folder naming
* README with setup instructions


## Project Tracking At the END of every session: - Update PROJECT-SUMMARY.md with what was built - Mark completed items as ✅ - Add new features discovered during build - Update "Last Updated" date

---

# Code Review Instructions

When reviewing code changes for this project, check:

## Security
- No API keys or secrets in code (should be in .env.local)
- No exposed credentials in commits

## Code Quality
- TypeScript types are correct
- No console.log statements left in production code
- Error handling is present

## Business Logic
- Underwriting calculations are accurate
- Safe Max uses correct constraints (ITV 50%, Coverage, End-of-Loan LTV)
- Email sends from proposals@firstnotecapital.com

## UI/UX
- Loading states exist
- Error states handled
- Mobile responsive