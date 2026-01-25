
// export const API_BASE = "/api";
export const API_BASE = "https://f4lguxbhmrrcqtc4qvcwns74qy0xzpzl.lambda-url.us-west-2.on.aws";

export const getAccessToken = () => localStorage.getItem('access_token');
export const setAccessToken = (token: string) => localStorage.setItem('access_token', token);
export const clearAccessToken = () => localStorage.removeItem('access_token');

export const getOpenAIKey = () => localStorage.getItem('openai_key');
export const setOpenAIKey = (key: string) => localStorage.setItem('openai_key', key);

export const authenticatedFetch = async (endpoint: string, options: RequestInit = {}): Promise<Response> => {
    const token = getAccessToken();
    const headers = new Headers(options.headers || {});

    if (token) {
        headers.set('X-Access-Token', token);
    }

    const openAIKey = getOpenAIKey();
    if (openAIKey) {
        headers.set('X-OpenAI-Key', openAIKey);
    }

    const config = {
        ...options,
        headers
    };

    const response = await fetch(`${API_BASE}${endpoint}`, config);

    if (response.status === 401) {
        clearAccessToken();
        window.dispatchEvent(new Event('auth-error'));
    }

    return response;
};
