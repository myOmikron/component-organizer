export function request(url, method = "GET", type = "json", body = "") {
    return new Promise(function (resolve, reject) {
        if (url.startsWith("/")) {
            const {host, protocol} = window.location;
            url = protocol + "//" + host + url;
        }

        const xhr = new XMLHttpRequest();
        xhr.open(method, url);
        xhr.responseType = type;

        if (type === "json") {
            xhr.setRequestHeader("Accept", "application/json");
            xhr.setRequestHeader("ContentType", "application/json");
            body = JSON.stringify(body);
        }

        xhr.onload = function (event) {
            if (xhr.status === 200) {
                resolve(xhr.response);
            } else {
                console.error(`Couldn't open '${url}': ${xhr.status} ${xhr.statusText}`);
                reject(`${xhr.status}: ${xhr.statusText}`);
            }
        };

        xhr.send(body);
    });
}

export function sleep(time) {
    return new Promise(function (resolve) {
        setTimeout(resolve, time);
    });
}
