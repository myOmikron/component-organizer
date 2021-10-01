import React from "../react.js";
import ReactDOM from "../react-dom.js";

const baseHost = window.location.protocol + "//" + window.location.host;
const e = React.createElement;

function getJson(url, method="GET", body) {
    return new Promise(((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.responseType = "json";
        xhr.open(method, url);
        xhr.setRequestHeader("Accept", "application/json");
        xhr.setRequestHeader("ContentType", "application/json");

        xhr.onreadystatechange = function () {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                try {
                    resolve(xhr.response);
                } catch (e) {
                    reject(e.toString());
                }
            }
        }.bind(this);

        if (body === undefined)
            xhr.send();
        else
            xhr.send(JSON.stringify(body));
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

function format(string, kwargs) {
    return string.replaceAll(/{+[^}]*}+/g, function(match) {
        const leadingBrackets = match.match(/^{+/)[0].length;
        const tailingBrackets = match.match(/}+$/)[0].length;
        let result = match.substring(leadingBrackets, match.length-tailingBrackets);
        if (leadingBrackets % 2 !== tailingBrackets % 2) {
            console.error("Unbalanced brackets");
        } else if (leadingBrackets % 2 !== 1) {
            // nothing to do
        } else {
            // _2 would be the conversion value "s", "r", "a" which stand for str, repr, ascii
            // since javascript doesn't have these functions just dump it
            const [_1, fieldName, _2, formatSpec] = result.match(/^([^!:]+)(![^:]+)?(:.+)?$/);

            // get the actual value
            let value = kwargs;
            const steps = fieldName.match(/(?:^[^.\[]+)|(?:\.\w+)|(?:\[\w+])/g);
            for (let i = 0; i < steps.length; i++) {
                let step = steps[i];
                if (step[0] === ".") {
                    step = step.substring(1);
                } else if (step[0] === "[") {
                    step = step.substring(1, step.length-1);
                }
                try {
                    value = value[step];
                } catch {
                    console.error(`Can't get ${fieldName}`);
                    value = "error";
                    break;
                }
            }
            result = value;

            // TODO: format value
        }
        return "{".repeat(Math.floor(leadingBrackets / 2)) + result + "}".repeat(Math.floor(tailingBrackets / 2));
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
        const state = this.state;
        const {itemId} = this.props;

        return e("div", {
            className: "flex-vertical",
        }, [
            e("h1", {}, format(this.state.template.name, {data: this.state.fields})),
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
            e("button", {
                onClick() {
                    getJson(baseHost + "/api/item/" + itemId, "put", {fields: state.fields})
                    .then(({success, result}) => {
                        if (success) {
                            setState(result);
                        } else {
                            console.error("Couldn't save item");
                        }
                    });
                }
            }, "Save"),
        ]);
    }
}

ReactDOM.render(React.createElement(EditItem, {itemId: 1}), document.getElementById("root"));
