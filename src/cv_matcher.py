#cv_matcher.py
import json
import re
from pathlib import Path


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

JOB_FILE = (
    BASE_DIR
    / "output"
    / "job"
    / "latest.json"
)

CV_PROFILES_FILE = (
    BASE_DIR
    / "output"
    / "cv"
    / "profiles.json"
)

CV_MANIFEST_FILE = (
    BASE_DIR
    / "output"
    / "cv"
    / "cv_manifest.json"
)

OUTPUT_DIR = (
    BASE_DIR
    / "output"
    / "application"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "selected_cv.json"
)


# ============================================================
# WEIGHTS
# ============================================================

LANGUAGE_WEIGHT = 30
ROLE_WEIGHT = 40
SKILL_WEIGHT = 20
EXPERIENCE_WEIGHT = 10


# ============================================================
# LOAD JSON
# ============================================================

def load_json(path: Path) -> dict:

    if not path.exists():

        raise FileNotFoundError(
            f"File tidak ditemukan:\n{path}"
        )

    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize(text: str) -> str:

    text = text.lower()

    text = text.replace(
        "&",
        " and "
    )

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def tokenize(text: str) -> set[str]:

    return set(
        normalize(text).split()
    )


# ============================================================
# KEYWORD MATCHING
# ============================================================

def keyword_similarity(
    source_terms: set[str],
    candidate_terms: set[str]
) -> float:

    if not source_terms:
        return 0.0

    matches = (
        source_terms
        .intersection(candidate_terms)
    )

    return (
        len(matches)
        / len(source_terms)
    )


# ============================================================
# LANGUAGE
# ============================================================

def language_score(
    job_language: str,
    cv_language: str
) -> float:

    job_language = (
        job_language or "unknown"
    ).lower()

    cv_language = (
        cv_language or "unknown"
    ).lower()

    if job_language == "english":

        return (
            100.0
            if cv_language == "english"
            else 0.0
        )

    if job_language == "indonesian":

        return (
            100.0
            if cv_language == "indonesian"
            else 0.0
        )

    # Unknown requirement.
    #
    # Indonesian is our default for
    # Indonesian job postings.

    if cv_language == "indonesian":
        return 100.0

    if cv_language == "english":
        return 70.0

    return 50.0


# ============================================================
# ROLE MATCH
# ============================================================

def role_score(
    job_position: str,
    manifest_roles: list[str],
    profile_roles: list[str]
) -> float:

    job_tokens = tokenize(
        job_position
    )

    if not job_tokens:
        return 0.0

    all_roles = (
        manifest_roles
        + profile_roles
    )

    best = 0.0

    for role in all_roles:

        role_tokens = tokenize(
            role
        )

        score = keyword_similarity(
            job_tokens,
            role_tokens
        )

        best = max(
            best,
            score
        )

    return best * 100


# ============================================================
# SKILL MATCH
# ============================================================

def skill_score(
    job: dict,
    profile: dict
) -> float:

    job_text = " ".join(
        [
            job.get(
                "position",
                ""
            ),

            *job.get(
                "requirements",
                []
            ),

            *job.get(
                "job_description",
                []
            )
        ]
    )

    cv_text = " ".join(
        [
            *profile.get(
                "skills",
                []
            ),

            *profile.get(
                "keywords",
                []
            )
        ]
    )

    return (
        keyword_similarity(
            tokenize(job_text),
            tokenize(cv_text)
        )
        * 100
    )


# ============================================================
# EXPERIENCE MATCH
# ============================================================

def experience_score(
    job: dict,
    profile: dict
) -> float:

    job_text = " ".join(
        [
            job.get(
                "position",
                ""
            ),

            *job.get(
                "requirements",
                []
            ),

            *job.get(
                "job_description",
                []
            )
        ]
    )

    job_tokens = tokenize(
        job_text
    )

    best = 0.0

    for experience in profile.get(
        "experience",
        []
    ):

        experience_text = " ".join(
            [
                experience.get(
                    "role",
                    ""
                ),

                experience.get(
                    "company",
                    ""
                ),

                *experience.get(
                    "responsibilities",
                    []
                ),

                *experience.get(
                    "skills",
                    []
                )
            ]
        )

        score = keyword_similarity(
            job_tokens,
            tokenize(
                experience_text
            )
        )

        best = max(
            best,
            score
        )

    return best * 100


# ============================================================
# MATCH SINGLE CV
# ============================================================

def match_cv(
    job: dict,
    manifest: dict,
    profile: dict
) -> dict:

    language = language_score(
        job.get(
            "language_requirement",
            "unknown"
        ),

        manifest.get(
            "language",
            profile.get(
                "language",
                "unknown"
            )
        )
    )

    role = role_score(
        job.get(
            "position",
            ""
        ),

        manifest.get(
            "target_roles",
            []
        ),

        profile.get(
            "target_roles",
            []
        )
    )

    skills = skill_score(
        job,
        profile
    )

    experience = experience_score(
        job,
        profile
    )

    total = (

        language
        * LANGUAGE_WEIGHT
        / 100

        +

        role
        * ROLE_WEIGHT
        / 100

        +

        skills
        * SKILL_WEIGHT
        / 100

        +

        experience
        * EXPERIENCE_WEIGHT
        / 100
    )

    return {

        "id": manifest["id"],

        "file": manifest["file"],

        "language": manifest.get(
            "language",
            "unknown"
        ),

        "scores": {

            "language": round(
                language,
                2
            ),

            "role": round(
                role,
                2
            ),

            "skills": round(
                skills,
                2
            ),

            "experience": round(
                experience,
                2
            )
        },

        "total_score": round(
            total,
            2
        )
    }


# ============================================================
# BUILD PROFILE LOOKUP
# ============================================================

def build_profile_lookup(
    profiles: dict
) -> dict:

    lookup = {}

    for record in profiles.get(
        "cvs",
        []
    ):

        lookup[
            record["id"]
        ] = record["profile"]

    return lookup


# ============================================================
# MATCH ALL ENABLED CVS
# ============================================================

def match_all(
    job: dict,
    manifest_data: dict,
    profiles: dict
) -> list[dict]:

    profile_lookup = (
        build_profile_lookup(
            profiles
        )
    )

    rankings = []

    for manifest in manifest_data.get(
        "cvs",
        []
    ):

        # ----------------------------------------------------
        # MANUAL CONTROL
        # ----------------------------------------------------

        if not manifest.get(
            "enabled",
            True
        ):

            continue

        cv_id = manifest["id"]

        if cv_id not in profile_lookup:

            print(
                f"⚠️ Profile tidak ditemukan: "
                f"{cv_id}"
            )

            continue

        profile = profile_lookup[
            cv_id
        ]

        result = match_cv(
            job,
            manifest,
            profile
        )

        rankings.append(
            result
        )

    rankings.sort(
        key=lambda item: item[
            "total_score"
        ],
        reverse=True
    )

    return rankings


# ============================================================
# SELECT BEST CV
# ============================================================

def select_best_cv(
    job: dict,
    rankings: list[dict]
) -> dict:

    if not rankings:

        raise RuntimeError(
            "Tidak ada CV yang eligible."
        )

    selected = rankings[0]

    job_language = (
        job.get(
            "language_requirement",
            "unknown"
        )
        .lower()
    )

    # --------------------------------------------------------
    # LANGUAGE SAFETY
    # --------------------------------------------------------

    if job_language == "english":

        english = [
            item
            for item in rankings
            if item["language"]
            == "english"
        ]

        if english:

            selected = english[0]

    elif job_language == "indonesian":

        indonesian = [
            item
            for item in rankings
            if item["language"]
            == "indonesian"
        ]

        if indonesian:

            selected = indonesian[0]

    else:

        # Unknown → prefer Indonesian
        # when the score difference is small.

        indonesian = [
            item
            for item in rankings
            if item["language"]
            == "indonesian"
        ]

        if indonesian:

            best_indonesian = indonesian[0]

            if (
                best_indonesian[
                    "total_score"
                ]
                >=
                selected[
                    "total_score"
                ] - 5
            ):

                selected = (
                    best_indonesian
                )

    return selected


# ============================================================
# SAVE RESULT
# ============================================================

def save_result(
    job: dict,
    selected: dict,
    rankings: list[dict]
) -> Path:

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    result = {

        "company": job.get(
            "company"
        ),

        "position": job.get(
            "position"
        ),

        "selected_cv": selected,

        "ranking": rankings
    }

    OUTPUT_FILE.write_text(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    return OUTPUT_FILE


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)

    print(
        "JOB APPLICATION AUTOMATION"
    )

    print(
        "STEP 5 - CV MATCHER"
    )

    print("=" * 60)

    # --------------------------------------------------------
    # JOB
    # --------------------------------------------------------

    print(
        "\n📄 Loading job..."
    )

    job = load_json(
        JOB_FILE
    )

    print(
        f"✅ {job.get('position')} "
        f"at {job.get('company')}"
    )

    # --------------------------------------------------------
    # MANIFEST
    # --------------------------------------------------------

    print(
        "\n📋 Loading CV manifest..."
    )

    manifest = load_json(
        CV_MANIFEST_FILE
    )

    enabled_count = sum(
        1
        for cv in manifest.get(
            "cvs",
            []
        )
        if cv.get(
            "enabled",
            True
        )
    )

    print(
        f"✅ {enabled_count} CV(s) enabled."
    )

    # --------------------------------------------------------
    # PROFILES
    # --------------------------------------------------------

    print(
        "\n🧠 Loading CV profiles..."
    )

    profiles = load_json(
        CV_PROFILES_FILE
    )

    print(
        "✅ CV profiles loaded."
    )

    # --------------------------------------------------------
    # MATCH
    # --------------------------------------------------------

    print(
        "\n🎯 Matching eligible CVs..."
    )

    rankings = match_all(
        job,
        manifest,
        profiles
    )

    if not rankings:

        print(
            "\n❌ No eligible CV found."
        )

        return

    selected = select_best_cv(
        job,
        rankings
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    output = save_result(
        job,
        selected,
        rankings
    )

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    print(
        "\n" + "=" * 60
    )

    print(
        "SELECTED CV"
    )

    print(
        "=" * 60
    )

    print(
        f"📄 File     : "
        f"{selected['file']}"
    )

    print(
        f"🌐 Language : "
        f"{selected['language']}"
    )

    print(
        f"🎯 Score    : "
        f"{selected['total_score']}"
    )

    print(
        "\nScore breakdown:"
    )

    for key, value in selected[
        "scores"
    ].items():

        print(
            f"  {key:<12}: {value}"
        )

    print(
        "\n" + "=" * 60
    )

    print(
        "CV RANKING"
    )

    print(
        "=" * 60
    )

    for index, item in enumerate(
        rankings,
        start=1
    ):

        print(
            f"{index}. "
            f"{item['file']} "
            f"→ "
            f"{item['total_score']}"
        )

    print(
        "\n📄 Saved to:"
    )

    print(
        output
    )

    print(
        "\n" + "=" * 60
    )

    print(
        "✅ STEP 5 COMPLETE"
    )

    print(
        "=" * 60
    )


if __name__ == "__main__":
    main()
