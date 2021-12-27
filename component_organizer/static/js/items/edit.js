import React from "../react.js";
import ReactDOM from "../react-dom.js";

import {request} from "../async.js";
import {LazyAutocomplete} from "../textinput.js";

const e = React.createElement;

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
            const steps = fieldName.match(/^[^.\[]+|\.\w+|\[\w+]/g);
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
            fields: {},  // {value: null, type: "string"}
            template: {
                id: -1,
                name: "Not loaded yet",
                fields: []
            },
            _toAdd: "",
            _reloading: false,
            _error: null,
            _errors: {},
        }

        this._addAttrInput = null;
        const path = window.location.pathname.split("/");
        this.apiEndpoint = "/api/item/" + path[path.length-1];
        request(this.apiEndpoint).then(this.setState.bind(this));

        this.setState = this.setState.bind(this);
    }

    renderField(key) {
        const {setState} = this;
        const isCustom = !this.state.template.fields.hasOwnProperty(key);
        const {[key]: field} = this.state.fields;
        return e(React.Fragment, {}, [
            e("tr", {key}, [
                e("td", {}, e("label", {htmlFor: key}, key)),
                e("td", {}, e(LazyAutocomplete, {
                    id: key,
                    url: "/api/common_values/" + key,
                    value: field ? field.value : "",
                    setValue(value) {setState(function(state) {
                        const {[key]: field, ...fields} = state.fields;
                        if (value !== "" || isCustom) {
                            fields[key] = {value, type: field ? field.type : state.template.fields[key]};
                        }
                        return {fields,};
                    });},
                })),
                isCustom ? e("td", {}, e("button", {
                    onClick() {
                        setState((state) => {
                            const {[key]: _, ...fields} = state.fields;
                            return {fields,};
                        });
                    },
                }, "Remove")) : null,
            ]),
            this.state._errors.hasOwnProperty(key) ? e("tr", {key: key + "_error"}, [
                e("td", {colspan: isCustom ? 3 : 2, style: {color: "red"}}, this.state._errors[key]),
            ]) : null,
        ]);
    }

    render() {
        const nonTempFields = [];
        for (const key in this.state.fields) {
            if (!this.state.template.fields.hasOwnProperty(key)) {
                nonTempFields.push(key);
            }
        }
        const setState = this.setState.bind(this);

        const formatFields = {};
        for (const [key, {value}] of Object.entries(this.state.fields)) {
            formatFields[key] = value;
        }

        return e("div", {
            className: "flex-vertical",
        }, [
            e("h1", {}, format(this.state.template.name, {data: formatFields})),
            e("table", {}, [
                ...Object.keys(this.state.template.fields).map(this.renderField.bind(this)),
            ]),
            e("h2", {}, "Additional Attributes"),
            e("table", {}, [
                ...nonTempFields.map(this.renderField.bind(this)),
                e("tr", {key: "_addAttr"}, [
                    e("td"),
                    e("td", {}, e("form", {
                        onSubmit: function (event) {
                            setState((state) => ({fields: {[state._toAdd]: "", ...state.fields}, _toAdd: ""}));
                            this._addAttrInput.focus();
                            event.preventDefault();
                        }.bind(this),
                    }, e("label", {}, e(LazyAutocomplete, {
                        url: "/api/common_keys",
                        value: this.state._toAdd,
                        setValue(value) {setState({_toAdd: value});},
                        reference: function (element) {this._addAttrInput = element;}.bind(this),
                    })))),
                    e("td", {}, e("button", {
                        onClick() {
                            // TODO how to enter type of new field
                            setState((state) => ({fields: {[state._toAdd]: {value: "", type: "string"}, ...state.fields}, _toAdd: ""}));
                        },
                    }, "Add")),
                ]),
            ]),
            e("button", {
                onClick: function() {
                    setState({_reloading: true, _error: null, _errors: {}});
                    request(this.apiEndpoint, "PUT", "json", {fields: this.state.fields})
                    .then(({result, error, errors}) => {
                        setState({_reloading: false, _error: error || null, _errors: errors || {}, ...result});
                    })
                    .catch((httpError) => {
                        console.error("Couldn't save item: "+httpError);
                    });
                }.bind(this),
            }, "Save"),
            this.state._error ? e("span", {style: {color: "red"}}, this.state._error) : this.state._reloading ? "Reloading..." : null,
        ]);
    }
}

ReactDOM.render(React.createElement(EditItem), document.getElementById("root"));
