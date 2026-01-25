import sys
import os

# Add app directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../app')))

from services.render_service import render_html

data = {
    "full_name": "John Doe",
    "phone": "555-0199",
    "email": "john@example.com",
    "linkedin": "linkedin.com/in/johndoe",
    "location": "New York, NY",
    "summary": "Experienced software engineer.",
    "experience_block": """
<ul>
<li>Developed a <strong>high-performance</strong> API using Python and Flask.</li>
<li>Managed a team of 5 engineers.</li>
<li>Implemented CI/CD pipelines using Jenkins and Docker.</li>
<li>This is a very long line that should definitely wrap around because it contains a lot of text and we want to see if the CSS handles it correctly without overflowing the container or looking weird with justification issues.</li>
</ul>
""",
    "skills_block": "<p>Python, HTML, CSS, JavaScript</p>"
}

try:
    output = render_html("app/templates/ats_resume.html", data)
    with open("test_output.html", "w") as f:
        f.write(output)
    print("Successfully rendered test_output.html")
except Exception as e:
    print(f"Error rendering template: {e}")
    sys.exit(1)
