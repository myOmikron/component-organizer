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

function TextInput(props) {
    const {value, setValue, ...otherProps} = props;

    return e("input", {
        value,
        onChange: (event) => {setValue(event.target.value);},
        ...otherProps,
    });
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
            _toAdd: "",
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
        const setState = this.setState.bind(this);

        return e("div", {
            className: "flex-vertical",
        }, [
            e("h1", {}, this.state.template.name),
            ...this.state.template.fields.map((key) => e("div", {key}, [
                e("label", {htmlFor: key}, key),
                e(TextInput, {
                    id: key,
                    value: this.state.fields[key],
                    setValue(value) {setState((state) => ({fields: {...state.fields, [key]: value}}))}
                }),
            ])),
            e("h2", {}, ["Additional Attributes"]),
            ...nonTempFields.map((key) => e("div", {key}, [
                e("label", {htmlFor: key}, key),
                e(TextInput, {
                    id: key,
                    value: this.state.fields[key],
                    setValue(value) {setState((state) => ({fields: {...state.fields, [key]: value}}))}
                }),
                e("button", {
                    onClick() {
                        setState((state) => {
                            const {[key]: toRemove, ...toKeep} = state.fields;
                            return {fields: toKeep};
                        });
                    },
                }, "Remove"),
            ])),
            e("div", {}, [
                e("label", {}, e(TextInput, {value: this.state._toAdd, setValue(value) {setState({_toAdd: value});}})),
                e("button", {
                    onClick() {
                        setState((state) => ({fields: {[state._toAdd]: "", ...state.fields}, _toAdd: ""}));
                    },
                }, "Add"),
            ]),
            e("button", {}, "Save"),
        ]);
    }
}

ReactDOM.render(React.createElement(EditItem, {itemId: 1}), document.getElementById("root"));
