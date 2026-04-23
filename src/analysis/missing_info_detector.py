from typing import Dict, Any, List, Optional
from ..models.cv_models import ExtractedCV

# ── Field definitions ─────────────────────────────────────────────────────────

_PERSONAL_CRITICAL = [
    ("email",   "Email address"),
    ("phone",   "Phone number"),
]
_PERSONAL_IMPORTANT = [
    ("address",        "Mailing/city address"),
    ("linkedin",       "LinkedIn profile URL"),
    ("google_scholar", "Google Scholar profile URL"),
    ("orcid",          "ORCID identifier"),
]

# ── Email templates ───────────────────────────────────────────────────────────

TEMPLATE_CONTACT = """\
Subject: Request for Missing Contact Information – {name}

Dear {name},

We are reviewing your application for the {position} position at {institution} \
and are pleased with your profile so far.

However, we noticed that the following contact details are missing from your CV:

{missing_items}

Please reply to this email with the above information at your earliest convenience \
so we may continue processing your application without delay.

Should you have any questions, do not hesitate to reach out.

Best regards,
{sender_name}
{sender_title}
{institution}
"""

TEMPLATE_ACADEMIC = """\
Subject: Request for Complete Academic Records – {name}

Dear {name},

Thank you for submitting your application for the {position} position at {institution}.

During our review, we found that the following academic details appear to be incomplete:

{missing_items}

Complete and verified academic records are a mandatory requirement for evaluation. \
We kindly ask that you provide the missing information within 5 working days.

If you have any questions regarding what is required, please contact us directly.

Best regards,
{sender_name}
{sender_title}
{institution}
"""

TEMPLATE_PUBLICATIONS = """\
Subject: Request for Publication Verification Details – {name}

Dear {name},

We are currently verifying the research output listed in your application for the \
{position} position at {institution}.

The following publication details are required for accurate evaluation:

{missing_items}

For each publication, please provide:
  • DOI or direct URL
  • Journal impact factor and indexing status (WoS / Scopus)
  • Complete author list with your authorship role

Please respond within 5 working days.

Best regards,
{sender_name}
{sender_title}
{institution}
"""

TEMPLATE_GENERAL = """\
Subject: Incomplete Application – Additional Information Required – {name}

Dear {name},

Thank you for applying for the {position} position at {institution}.

To complete the review of your application, we require the following additional \
information:

{missing_items}

Kindly provide these details at your earliest convenience. Applications that remain \
incomplete beyond 5 working days may not be considered for the current cycle.

Best regards,
{sender_name}
{sender_title}
{institution}
"""


def _fmt_list(items: List[str]) -> str:
    return "\n".join(f"  • {item}" for item in items)


class MissingInfoDetector:

    def detect(self, cv: ExtractedCV) -> Dict[str, Any]:
        missing: Dict[str, List[str]] = {
            "contact_critical": [],
            "contact_important": [],
            "education": [],
            "experience": [],
            "publications": [],
        }

        pi = cv.personal_info

        # ── Personal info ─────────────────────────────────────────────────────
        for field, label in _PERSONAL_CRITICAL:
            if not getattr(pi, field):
                missing["contact_critical"].append(label)

        for field, label in _PERSONAL_IMPORTANT:
            if not getattr(pi, field):
                missing["contact_important"].append(label)

        # ── Education records ─────────────────────────────────────────────────
        for i, edu in enumerate(cv.education, 1):
            label = f"{edu.degree_title or 'Degree ' + str(i)} ({edu.institution or 'unknown institution'})"
            if edu.grade_value is None:
                missing["education"].append(f"{label} — grade/marks not provided")
            if edu.start_year is None:
                missing["education"].append(f"{label} — start year missing")
            if edu.end_year is None:
                missing["education"].append(f"{label} — end/expected year missing")

        # ── Experience records ────────────────────────────────────────────────
        for exp in cv.experience:
            label = f"{exp.job_title} at {exp.organization}"
            if exp.start_date is None:
                missing["experience"].append(f"{label} — start date missing")
            if not exp.is_current and exp.end_date is None:
                missing["experience"].append(f"{label} — end date missing (not marked as current)")

        # ── Publications ──────────────────────────────────────────────────────
        for pub in cv.journal_publications:
            short = pub.title[:50] + "…" if len(pub.title) > 50 else pub.title
            issues = []
            if not pub.doi:
                issues.append("DOI missing")
            if not pub.issn:
                issues.append("ISSN missing")
            if pub.impact_factor is None:
                issues.append("impact factor not stated")
            if pub.quartile is None:
                issues.append("quartile not stated")
            if pub.is_wos_indexed is None and pub.is_scopus_indexed is None:
                issues.append("indexing status unknown")
            if issues:
                missing["publications"].append(f'"{short}" — {", ".join(issues)}')

        for pub in cv.conference_publications:
            short = pub.title[:50] + "…" if len(pub.title) > 50 else pub.title
            issues = []
            if not pub.doi:
                issues.append("DOI missing")
            if pub.is_indexed is None:
                issues.append("indexing status unknown")
            if issues:
                missing["publications"].append(f'"{short}" — {", ".join(issues)}')

        # ── Summary flags ─────────────────────────────────────────────────────
        all_missing = (
            missing["contact_critical"]
            + missing["contact_important"]
            + missing["education"]
            + missing["experience"]
            + missing["publications"]
        )
        has_critical = len(missing["contact_critical"]) > 0

        return {
            "has_missing_info": len(all_missing) > 0,
            "has_critical_missing": has_critical,
            "missing_by_category": missing,
            "total_missing_fields": len(all_missing),
            "all_missing": all_missing,
        }

    def get_email_template(
        self,
        missing_info: Dict[str, Any],
        name: str,
        position: str = "the advertised position",
        institution: str = "our institution",
        sender_name: str = "HR Committee",
        sender_title: str = "Recruitment Office",
    ) -> Dict[str, str]:
        """
        Return filled-in sample email templates relevant to the detected gaps.
        Always returns at least the general template; adds category-specific ones
        when relevant missing fields exist.
        """
        by_cat = missing_info["missing_by_category"]
        ctx = dict(
            name=name,
            position=position,
            institution=institution,
            sender_name=sender_name,
            sender_title=sender_title,
        )

        templates: Dict[str, str] = {}

        contact_items = by_cat["contact_critical"] + by_cat["contact_important"]
        if contact_items:
            templates["contact"] = TEMPLATE_CONTACT.format(
                missing_items=_fmt_list(contact_items), **ctx
            )

        if by_cat["education"]:
            templates["academic"] = TEMPLATE_ACADEMIC.format(
                missing_items=_fmt_list(by_cat["education"]), **ctx
            )

        if by_cat["publications"]:
            templates["publications"] = TEMPLATE_PUBLICATIONS.format(
                missing_items=_fmt_list(by_cat["publications"]), **ctx
            )

        all_items = missing_info["all_missing"]
        templates["general"] = TEMPLATE_GENERAL.format(
            missing_items=_fmt_list(all_items) if all_items else "  • No specific items — application appears complete.",
            **ctx,
        )

        return templates

    def generate_personalized_email(
        self,
        cv: ExtractedCV,
        missing_info: Dict[str, Any],
        api_key: str,
        model_name: str = "gemini-2.5-flash-lite",
        position: str = "the advertised position",
        institution: str = "our institution",
        sender_name: str = "HR Committee",
        sender_title: str = "Recruitment Office",
    ) -> str:
        """
        Use an LLM to generate a professional, personalised email based on
        the detected missing fields and candidate profile.
        """
        from google import genai

        if not missing_info["has_missing_info"]:
            return "No missing information detected — no email required."

        all_missing = missing_info["all_missing"]
        name = cv.personal_info.full_name
        highest_degree = (cv.education[-1].degree_title if cv.education else "degree not specified")

        prompt = f"""You are an HR officer at {institution} drafting a professional email to a job applicant.

Applicant name: {name}
Highest qualification: {highest_degree}
Position applied for: {position}

The following information is missing from their CV:
{chr(10).join(f"- {item}" for item in all_missing)}

Write a single, polished, professional email (subject line + body) that:
1. Opens with a positive acknowledgement of their application
2. Clearly lists the missing information needed
3. States a 5 working-day response window
4. Closes professionally

Sign off as:
{sender_name}
{sender_title}
{institution}

Return only the email text, no additional commentary."""

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model=model_name, contents=prompt)
        return response.text