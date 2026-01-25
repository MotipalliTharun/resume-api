# {{ full_name }}
{% if phone %}{{ phone }}{% endif %}{% if email %}{% if phone %} | {% endif %}{{ email }}{% endif %}{% if linkedin %}{% if phone or email %} | {% endif %}{{ linkedin }}{% endif %}{% if portfolio %}{% if phone or email or linkedin %} | {% endif %}{{ portfolio }}{% endif %}

## SUMMARY
{{ summary }}

## SKILLS
{{ skills_block }}

## WORK EXPERIENCE
{{ experience_block }}

{% if projects_block %}
## PROJECTS
{{ projects_block }}
{% endif %}

{% if certifications_block %}
## CERTIFICATIONS
{{ certifications_block }}
{% endif %}

{% if achievements_block %}
## ACHIEVEMENTS
{{ achievements_block }}
{% endif %}

## EDUCATION
{{ education_block }}



