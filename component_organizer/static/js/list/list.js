import React from "../react.js";
import ReactDOM from "../react-dom.js";

import TextInput from "../textinput.js";
import {request} from "../async.js";

const e = React.createElement;

class ItemList extends React.Component {

    constructor(props) {
        super(props);

        const tempQuery = window.location.search.match(/[?&]query=([^&]+)/);
        this.state = {
            query: tempQuery ? decodeURIComponent(tempQuery[1].replace(/\+/g, ' ')) : "",
            commonKeys: [],
            suggestions: [],
            suggestionIndex: -1,
            showSuggestions: false,
        }

        // request the common keys
        request("/api/common_keys").then(function (commonKeys) {
            this.setState({commonKeys,});
        }.bind(this));

        // reference to the <input> for search queries
        this.queryInput = null;
        this.suggestResolve = null;
        this.suggestPromise = null;
    }

    get currentQuery() {
        const queries = this.state.query.split(/ *(?<!\\), */);
        const query = queries[queries.length-1];
        const keyValue = query.split(/ *(?:=|<=|>=|<|>) */)
        return {
            query,
            key: keyValue[0],
            value: keyValue.length > 1 ? keyValue[1] : null,
        }
    }

    suggestKey(state) {
        let {key, value} = this.currentQuery;
        if (value !== null) {
            return [];
        }
        key = key.toLowerCase();
        const {suggestionIndex} = state;
        const suggestions = state.commonKeys.filter((commonKey) => commonKey.toLowerCase().startsWith(key));
        return {suggestions,
                showSuggestions: true,
                suggestionIndex: suggestionIndex >= suggestions.length ? suggestions.length - 1 : suggestionIndex,
        };
    }

    componentDidUpdate(prevProps, prevState) {
        if (prevState.query !== this.state.query) {
            if (this.suggestResolve !== null) {
                this.suggestResolve();
            }
            this.suggestPromise = new Promise(function (resolve) {
                this.suggestResolve = resolve;
                this.setState(this.suggestKey.bind(this));
            }.bind(this));
        }
    }

    complete() {
        const {key, value} = this.currentQuery;
        const {suggestions, suggestionIndex, query} = this.state;
        if (value !== null || suggestionIndex < 0) return false;
        const suggestion = suggestions[suggestionIndex];
        const newQuery = query.substr(0, query.length - key.length) + suggestion;
        if (newQuery === query) {
            return false;
        } else {
            this.setState({query: newQuery, showSuggestions: false});
            this.queryInput.focus();
            return true;
        }
    }

    render() {
        const setState = this.setState.bind(this);
        const complete = this.complete.bind(this);
        const setIndex = function (delta) {
            setState((state) => ({suggestionIndex: (state.suggestionIndex+delta)%state.suggestions.length}));
        }
        const {showSuggestions, suggestions} = this.state;

        return e("div", {}, [
            showSuggestions && suggestions.length > 0 ?  e("div", {
                style: {
                    position: "fixed",
                    left: this.queryInput.offsetLeft + "px",
                    top: this.queryInput.offsetTop + this.queryInput.offsetHeight + "px",
                    background: "#15202b",
                    border: "1px solid",
                    margin: "5px",
                }
            }, suggestions.map((key, index) => e("div", {
                style: {
                    padding: "2px",
                    background: index === this.state.suggestionIndex ? "#1f2f3f" : "",
                    cursor: "pointer",
                },
                onMouseEnter() {setState({suggestionIndex: index})},
                onMouseDown: this.complete.bind(this),
            }, key))) : null,
            e("a", {href: "/item/new"}, "Create new item"),
            e("form", {}, [
                e("label", {}, e(TextInput, {
                    reference: function (element) {this.queryInput = element;}.bind(this),
                    name: "query",
                    value: this.state.query,
                    onKeyDown(event) {
                        if (showSuggestions) {
                            const {key} = event;
                            if (key === "ArrowDown")
                                setIndex(+1);
                            else if (key === "ArrowUp")
                                setIndex(-1);
                            else if (key === "Tab") {
                                if (suggestions.length > 1)
                                    setIndex(+1);
                                else
                                    complete();
                                event.preventDefault();
                            }
                            else if (key === "Enter") {
                                if (complete()) {
                                    event.preventDefault();
                                }
                            }
                        }
                    },
                    onFocus() {setState({showSuggestions: true});},
                    onBlur() {setState({showSuggestions: false});},
                    setValue(value) {setState({query: value});},
                })),
                e("input", {type: "submit", value: "Search"})
            ]),
            e("table", {}, [
                e("thead", {}, e("tr", {}, [
                    e("th", {}, "Name"),
                    e("th", {}, "#"),
                ])),
                e("tbody", {}, document.items.map(({name, url, amount}) => (
                    e("tr", {}, [
                        e("td", {}, e("a", {href: url}, name)),
                        e("td", {}, amount),
                    ])
                ))),
            ]),
        ]);
    }
}

ReactDOM.render(React.createElement(ItemList), document.getElementById("root"));
