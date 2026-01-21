import re

class KeywordStandardizer:
    # Groups of synonymous tech terms
    # We will check the JD for any of these. If found, that specific spelling becomes the "Canonical" one.
    # All other variations in the resume will be replaced by that Canonical one.
    TECH_GROUPS = [
        {"react", "reactjs", "react.js", "react.JS", "react js"},
        {"node", "nodejs", "node.js", "node js"},
        {"aws", "amazon web services"},
        {"dotnet", ".net", "dot net"},
        {"c#", "csharp", "c sharp"},
        {"golang", "go", "go lang"},
        {"postgresql", "postgres"},
        {"mongodb", "mongo"},
        {"typescript", "ts"},
        {"javascript", "js", "es6"},
        {"springboot", "spring boot", "spring-boot"},
        {"kubernetes", "k8s"},
        {"docker", "containerization"},
        {"gcp", "google cloud platform", "google cloud"},
        {"azure", "microsoft azure"},
        {"rest api", "restful api", "rest", "restful"},
        {"graphql", "graph ql"},
        {"nextjs", "next.js", "next js"},
        {"vuejs", "vue.js", "vue"},
        {"angular", "angularjs"},
        {"expressjs", "express.js", "express"},
        {"django", "python django"},
        {"flask", "python flask"},
        {"ruby on rails", "rails", "ror"},
        {"ci/cd", "cicd", "continuous integration"},
        {"jenkins", "jenkins ci"},
        {"github actions", "gh actions"},
        {"terraform", "hashicorp terraform"},
    ]

    @staticmethod
    def normalize_text(resume_text: str, jd_text: str) -> str:
        """
        Scans JD for preferred spellings and enforces them in the resume text.
        """
        normalized_text = resume_text
        jd_lower = jd_text.lower()
        
        # 1. Build a dynamic replacement map based on JD content
        replacements = {}
        
        for group in KeywordStandardizer.TECH_GROUPS:
            # Find which variation is used in the JD (prefer longest match to avoid 'go' vs 'golang' false positives if possible, or just first found)
            # Actually, we want the EXACT casing from the JD.
            
            best_token = None
            found_index = -1
            
            for term in group:
                # Search case-insensitive
                pattern = re.compile(re.escape(term), re.IGNORECASE)
                match = pattern.search(jd_text)
                if match:
                    # Found a term! Use the EXACT matching text from JD as canonical
                     best_token = match.group(0) 
                     break # Stop after finding the first valid match in this group (e.g. if JD has ReactJS, stick to it)
            
            if best_token:
                # If JD has a preferred token, map all OTHER group members to this token
                for term in group:
                    # Don't replace the token with itself (though strictly okay)
                    # We map the lowercase version of the term to the best_token replacement
                    replacements[term] = best_token

        # 2. Apply replacements
        # We search case-insensitively for the 'keys' in resume_text, and replace with 'values'
        if not replacements:
            return normalized_text

        # Iterate and replace. 
        # Note: A naive iteration might be slow or overlap. 
        # But given the list size, sequential replacement is acceptable.
        for term_lower, replacement in replacements.items():
            # Regex to match whole word/phrase case-insensitively
            # \b might fail for ".net" or "c#", so we need careful boundaries.
            # "react.js" has dot. 
            # We use custom boundary check or just standard \b for words, but for symbols proceed carefully.
            
            safe_term = re.escape(term_lower)
            # We want to match this term in the resume text, ignoring case
            pattern = re.compile(rf"(?i)\b{safe_term}\b") 
            
            # Special handling for C# or .NET where \b is tricky?
            # \b matches between \w and \W, or ^ and \w etc.
            # . is \W, # is \W. So \b.net\b might match " .net " but not ".net" if at start of string?
            # Let's trust \b for now but maybe just use whitespace boundaries for symbol-heavy ones if needed.
            # Actually, `re.sub` is fine.
            
            normalized_text = pattern.sub(replacement, normalized_text)
            
        return normalized_text
