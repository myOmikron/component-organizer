import React from "../react.js";
import ReactDOM from "../react-dom.js";

const baseHost = window.location.protocol + "//" + window.location.host;
const e = React.createElement;


function getJson(url, method="GET") {
    return new Promise(((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.responseType = "json";
        xhr.open(method, url);

        xhr.onreadystatechange = function () {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                try {
                    resolve(xhr.response);
                } catch (e) {
                    reject(e.toString());
                }
            }
        }.bind(this);

        xhr.send();
    }));
}


class EditItem extends React.Component {

    constructor(props) {
        super(props);

        this.state= {
            id: -1,
            category: -1,
            fields: {},
            template: {
                id: -1,
                name: "Not loaded yet",
                fields: []
            },
        }

        const {itemId} = props;
        getJson(baseHost + "/api/item/" + itemId).then(this.setState.bind(this));
    }

    render() {
        const nonTempFields = [];
        for (const key in this.state.fields) {
            if (!this.state.template.fields.includes(key)) {
                nonTempFields.push(key);
            }
        }

        return e("div", {
            className: "flex-vertical",
        }, [
            e("h1", {}, this.state.template.name),
            ...this.state.template.fields.map((key) => e("div", {}, [
                e("label", {htmlFor: key}, key),
                e("input", {id: key, name: "set_"+key, value: this.state.fields[key]})
            ])),
            e("h2", {}, ["Additional Attributes"]),
            ...nonTempFields.map((key) => e("div", {}, [
                e("label", {htmlFor: key}, key),
                e("input", {id: key, name: "set_"+key, value: this.state.fields[key]}),
                e("button", {}, "Remove"),
            ])),
            e("div", {}, [
                e("label", {}, e("input")),
                e("button", {}, "Add"),
            ]),
            e("button", {}, "Save"),
        ]);
    }
}

ReactDOM.render(React.createElement(EditItem, {itemId: 1}), document.getElementById("root"));
