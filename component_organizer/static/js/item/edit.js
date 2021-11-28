import React from "../react.js";
import ReactDOM from "../react-dom.js";

import {request} from "../async.js";
import TextInput from "../textinput.js";

const e = React.createElement;

function parse(string) {
    const number = parseFloat(string.match(/^[+-]?\d*(?:\.\d+)?(?:e[+-]?\d+)?$/));
    return isNaN(number) ? string : number;
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

        this._addAttrInput = null;
        const path = window.location.pathname.split("/");
        this.apiEndpoint = "/api/item/" + path[path.length-1];
        request(this.apiEndpoint).then(this.setState.bind(this));
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
            e("h1", {}, format(this.state.template.name, {data: this.state.fields})),
            e("table", {}, [
                ...this.state.template.fields.map((key) => e("tr", {key}, [
                    e("td", {}, e("label", {htmlFor: key}, key)),
                    e("td", {}, e(TextInput, {
                        id: key,
                        value: this.state.fields[key],
                        setValue(value) {setState((state) => ({fields: {...state.fields, [key]: parse(value)}}))}
                    })),
                ])),
            ]),
            e("h2", {}, "Additional Attributes"),
            e("table", {}, [
                ...nonTempFields.map((key) => e("tr", {key}, [
                    e("td", {}, e("label", {htmlFor: key}, key)),
                    e("td", {}, e(TextInput, {
                        id: key,
                        value: this.state.fields[key],
                        setValue(value) {setState((state) => ({fields: {...state.fields, [key]: parse(value)}}))}
                    })),
                    e("td", {}, e("button", {
                        onClick() {
                            setState((state) => {
                                const {[key]: toRemove, ...toKeep} = state.fields;
                                return {fields: toKeep};
                            });
                        },
                    }, "Remove")),
                ])),
                e("tr", {key: "_addAttr"}, [
                    e("td"),
                    e("td", {}, e("form", {
                        onSubmit: function (event) {
                            setState((state) => ({fields: {[state._toAdd]: "", ...state.fields}, _toAdd: ""}));
                            this._addAttrInput.focus();
                            event.preventDefault();
                        }.bind(this),
                    }, e("label", {}, e(TextInput, {
                        value: this.state._toAdd,
                        setValue(value) {setState({_toAdd: value});},
                        reference: function (element) {this._addAttrInput = element;}.bind(this),
                    })))),
                    e("td", {}, e("button", {
                        onClick() {
                            setState((state) => ({fields: {[state._toAdd]: "", ...state.fields}, _toAdd: ""}));
                        },
                    }, "Add")),
                ]),
            ]),
            e("button", {
                onClick: function() {
                    request(this.apiEndpoint, "PUT", "json", {fields: this.state.fields})
                    .then(({success, result}) => {
                        if (success) {
                            setState(result);
                        } else {
                            console.error("Couldn't save item");
                        }
                    });
                }.bind(this),
            }, "Save"),
        ]);
    }
}

ReactDOM.render(React.createElement(EditItem), document.getElementById("root"));
