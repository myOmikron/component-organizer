import React from "../react.js";
import ReactDOM from "../react-dom.js";

import TextInput from "../textinput.js";
import {request} from "../async.js";

const e = React.createElement;

class ItemList extends React.Component {

    constructor(props) {
        super(props);

        let tempQuery = window.location.search.match(/[?&]query=([^&]+)/);
        tempQuery = tempQuery ? decodeURIComponent(tempQuery[1].replace(/\+/g, ' ')) : "";
        this.state = {
            query: "",
            queryKey: "",
            queryValue: null, // might be null, when a key is currently entered into query
            commonKeys: [],
            suggestions: null, // is only null at start and array of strings after first change to query
            suggestionIndex: -1,
            showSuggestions: false,
            ...this.setQuery(tempQuery), // populate query, queryKey, queryValue using the http GET query
        }

        // request the common keys
        request("/api/common_keys").then(function (commonKeys) {
            this.setState({commonKeys,});
        }.bind(this));

        // reference to the <input> for search queries
        this.queryInput = null;
    }

    setQuery(query) {
        const queries = query.split(/ *(?<!\\), */);
        const keyValue = queries[queries.length-1].split(/ *(?:=|<=|>=|<|>) */);
        return {query, queryKey: keyValue[0], queryValue: keyValue.length > 1 ? keyValue[1] : null};
    }

    componentDidUpdate(prevProps, prevState) {
        if (this.state.query !== prevState.query) {
            // Get the old/new value currently entered in the query and the set of their possible suggestions
            // (Basically select whether a key or a value is entered right now)
            let oldValue, newValue, filterSet;
            if (this.state.queryValue === null) {
                oldValue = prevState.queryKey;
                newValue = this.state.queryKey;
                filterSet = this.state.commonKeys;
            } else {
                oldValue = prevState.queryValue;
                newValue = this.state.queryValue;
                filterSet = ["a1", "b2", "c3"];  // get actual values for key
            }

            // Exit if nothing changed
            if (oldValue === newValue) return;
            // Reduce filterSet if possible
            else if (this.state.suggestions !== null && newValue.startsWith(oldValue)) {
                filterSet = this.state.suggestions;
            }

            // Filter and set new suggestions
            newValue = newValue.toLowerCase();
            const {suggestionIndex} = this.state;
            const suggestions = filterSet.filter((commonValue) => commonValue.toLowerCase().startsWith(newValue));
            this.setState({
                suggestions,
                showSuggestions: true,
                suggestionIndex: suggestionIndex >= suggestions.length ? suggestions.length - 1 : suggestionIndex,
            });
        }
    }

    complete() {
        const {suggestions, suggestionIndex, query, queryKey, queryValue} = this.state;
        if (suggestionIndex < 0) return false;
        const suggestion = suggestions[suggestionIndex];

        let newQuery;
        if (queryValue !== null) {
            newQuery = query.substr(0, query.length - queryValue.length) + suggestion;
        } else {
            newQuery = query.substr(0, query.length - queryKey.length) + suggestion;
        }

        if (newQuery === query) {
            return false;
        } else {
            this.setState({showSuggestions: false, ...this.setQuery(newQuery)});
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
                    setValue: function(value) {this.setState(this.setQuery(value));}.bind(this),
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
