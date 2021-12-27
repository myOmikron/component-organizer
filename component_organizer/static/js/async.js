export async function request(url, method = "GET", type = "json", body = "") {
    // Resolve relative urls
    if (url.startsWith("/")) {
        const {host, protocol} = window.location;
        url = protocol + "//" + host + url;
    }

    // Set headers
    const headers = {};
    if (type === "json") {
        headers["Accept"] = "application/json";
        headers["ContentType"] = "application/json";
        body = JSON.stringify(body);
    }

    // Send request
    const response = await fetch(url, {
        method,
        headers,
        body: (method === "HEAD" || method === "GET") ? undefined : body,
    });

    // Parse result
    if (type === "json") {
        try {
            return await response.json();
        } catch (SyntaxError) {
            return Promise.reject(`${response.status} - ${response.statusText}`);
        }
    } else {
        return await response.text();
    }
}

export function sleep(time) {
    return new Promise(function (resolve) {
        setTimeout(resolve, time);
    });
}
