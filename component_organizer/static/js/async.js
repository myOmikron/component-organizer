export function request(url, method = "GET", type = "json") {
    return new Promise(function (resolve, reject) {
        if (url.startsWith("/")) {
            const {host, protocol} = window.location;
            url = protocol + "//" + host + url;
        }
        const xhr = new XMLHttpRequest();
        xhr.open(method, url);
        xhr.responseType = type;
        xhr.onload = function (event) {
            if (xhr.status === 200) {
                resolve(xhr.response);
            } else {
                console.error(`Couldn't open '${url}': ${xhr.status} ${xhr.statusText}`);
                reject(`${xhr.status}: ${xhr.statusText}`);
            }
        };
        xhr.send();
    });
}

export function sleep(time) {
    return new Promise(function (resolve) {
        setTimeout(resolve, time);
    });
}
