import { cookies, headers } from 'next/headers';

export async function fetchApi<T>(path: string): Promise<T> {
    const cookieStore = await cookies();
    const response = await fetch(`${'http://localhost:6456'}${path}`, {
        headers: {
            Cookie: `saas_microservices_authed_user=${
                cookieStore.get('saas_microservices_authed_user')?.value
            }`,
        },
    });
    return response.json() as Promise<T>;
}
