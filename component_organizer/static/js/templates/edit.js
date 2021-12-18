import React from "../react.js";
import ReactDOM from "../react-dom.js";

import {request} from "../async.js";
import TextInput, {LazyAutocomplete} from "../textinput.js";
import {ContainerTree, SplitScreen} from "../trees.js";

const e = React.createElement;

class EditTemplate extends React.Component {

    constructor(props) {
        super(props);

        this.state= {
            id: -1,
            name: "Not loaded yet",
            item_name: "",
            fields: [],
            ownFields: [],
            isOwnField: {},
            parent: {
                id: -1,
                name: "",
            },
            _toAdd: "",
        }

        this.apiEndpoint = "/api/template/" + this.props.template;
        const setState = this.setState.bind(this);
        request(this.apiEndpoint).then((state) => {
            const isOwnField = {};
            state.fields.map((field) => {isOwnField[field] = false;});
            state.ownFields.map((field) => {isOwnField[field] = true;});
            setState({
                isOwnField,
                ...state,
            });
        });

        this._addAttrInput = null;
    }

    render() {
        const setState = this.setState.bind(this);
        const {openTemplate} = this.props;
        const {parent} = this.state;

        const ownFields = this.state.fields.filter((field) => this.state.isOwnField[field]);
        const parentFields = this.state.fields.filter((field) => !this.state.isOwnField[field]);

        function removeField(field) {
            setState(function (state) {
                if (state.isOwnField[field]) {
                    const {[field]: _, ...isOwnField} = state.isOwnField;
                    function filter(item) {
                        return item !== field;
                    }
                    return {
                        isOwnField,
                        fields: state.fields.filter(filter),
                        ownFields: state.ownFields.filter(filter),
                    }
                } else {
                    return {};
                }
            });
        }
        function addField() {
            setState(function (state) {
                if (!state.isOwnField.hasOwnProperty(state._toAdd)) {
                    return {
                        fields: [...state.fields, state._toAdd],
                        ownFields: [...state.ownFields, state._toAdd],
                        isOwnField: {...state.isOwnField, [state._toAdd]: true},
                        _toAdd: "",
                    }
                } else {
                    return {};
                }
            });
        }


        return e("div", {
            className: "flex-vertical",
        }, [
            e("h1", {}, this.state.name),
            e(TextInput, {value: this.state.item_name, setValue(value) {setState({item_name: value});}}),
            e("h1", {onClick() {openTemplate(parent.id);},}, ["Inherited from ", parent.name]),
            parentFields.length > 0 ? e("ul", {}, parentFields.map((field) => e("li", {}, field))) : "Nothing",
            e("h1", {}, "Own fields"),
            e("table", {}, [
                ownFields.map((field) => e("tr", {}, [
                    e("td", {}, field),
                    e("td", {}, e("button", {onClick() {removeField(field);}}, "Remove"))
                ])),
                e("tr", {}, [
                    e("td", {}, e("form", {
                        onSubmit: function (event) {
                            addField();
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
                        onClick: addField,
                    }, "Add")),
                ]),
            ]),
            e("button", {
                onClick: function () {
                    request(this.apiEndpoint, "PUT", "json", {item_name: this.state.item_name, fields: this.state.ownFields})
                        .then(({success, result}) => {
                            if (success) {
                                setState(result);
                            } else {
                                console.error("Couldn't save template");
                            }
                        });
                }.bind(this),
            }, "Save"),
            e("button", {
                onClick: function () {
                    request(this.apiEndpoint, "DELETE")
                        .then(({success}) => {
                            if (success) {
                                window.location = "/template/" + this.state.parent;
                            } else {
                                console.error("Couldn't delete template");
                            }
                        });
                }.bind(this),
            }, "Delete"),
        ]);
    }
}
EditTemplate.defaultProps = {
    template: 0,
    openTemplate: function (id) {console.log("Open template with id: ", id)},
};

class NewTemplate extends React.Component {

    constructor(props) {
        super(props);

        this.state = {
            name: "",
        };
    }

    send() {
        request("/api/template", "POST", "json", {name: this.state.name, parent: this.props.parent}).then(({success, result}) => {
            if (success) {
                window.location = "/template/" + result.id;
            } else {
                console.error("Couldn't create template");
            }
        });
    }

    render() {
        const send = this.send.bind(this);
        return e("div", {className: "flex-vertical"}, [
            e("form", {
                onSubmit(event) {
                    event.preventDefault();
                    send();
                }
            }, e("label", {}, ["Template Name ", e(TextInput, {
                value: this.state.name,
                setValue: function (value) {this.setState({name: value});}.bind(this),
            })])),
            e("button", {onclick: send}, "Create")
        ]);
    }
}
NewTemplate.defaultProps = {
    parent: 0,
};

class Main extends React.Component {

    constructor(props) {
        super(props);

        const path = window.location.pathname.split("/");
        const template = parseInt(path[path.length - 1]);
        this.initialTemplate = isNaN(template) ? 0 : template;
        this.state = {
            currentTemplate: this.initialTemplate,
            createNewTemplate: false,
        };
    }

    render() {
        const setState = this.setState.bind(this);
        const openTemplate = function (id) {setState({currentTemplate: id, createNewTemplate: false});};

        return e(SplitScreen, {}, [
            e(ContainerTree, {
                key: "containerTree",
                openContainer: openTemplate,
                createContainer(id) {setState({currentTemplate: id, createNewTemplate: true});},
                initiallyOpened: [this.initialTemplate],
                ...this.props,
            }),
            this.state.createNewTemplate ? e(NewTemplate, {
                key: "newTemplate" + this.state.currentTemplate,
                parent: this.state.currentTemplate,
            }) : e(EditTemplate, {
                key: "template" + this.state.currentTemplate,
                template: this.state.currentTemplate,
                openTemplate,
            }),
        ]);
    }
}

ReactDOM.render(e(Main, document.props), document.getElementById("root"));
