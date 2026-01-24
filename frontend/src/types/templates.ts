export interface ResumeTemplate {
    id: string;
    name: string;
    class: string;
    description: string;
}

export const AVAILABLE_TEMPLATES: ResumeTemplate[] = [
    {
        id: 'standard',
        name: 'Standard ATS',
        class: 'ats-template-standard',
        description: 'Clean, simple, and maximize readability. Best for most industries.'
    },
    {
        id: 'modern',
        name: 'Modern Clean',
        class: 'ats-template-modern',
        description: 'Sleek sans-serif fonts with distinct headers.'
    },
    {
        id: 'executive',
        name: 'Executive Serif',
        class: 'ats-template-executive',
        description: 'Formal serif typography for senior roles.'
    }
];
