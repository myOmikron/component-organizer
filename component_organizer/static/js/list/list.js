import React from "../react.js";
import ReactDOM from "../react-dom.js";

import {AutoComplete} from "../textinput.js";
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
            commonValues: {}, // map from key to array of values
            suggestions: null, // is only null at start and array of strings after first change to query
            suggestionIndex: -1,
            showSuggestions: false,
            ...this.setQuery(tempQuery), // populate query, queryKey, queryValue using the http GET query
        }

        // request the common keys
        request("/api/common_keys").then(function (commonKeys) {
            this.setState({commonKeys,});
        }.bind(this));
    }

    setQuery(query) {
        const queries = query.split(/ *(?<!\\), */);
        const keyValue = queries[queries.length-1].split(/ *(?:=|<=|>=|<|>) */);
        return {query, queryKey: keyValue[0], queryValue: keyValue.length > 1 ? keyValue[1] : null};
    }

    componentDidUpdate(prevProps, prevState) {
        const gotNewValues = this.state.commonValues !== prevState.commonValues;
        if (gotNewValues || this.state.query !== prevState.query) {
            // Get the old/new value currently entered in the query and the set of their possible suggestions
            // (Basically select whether a key or a value is entered right now)
            let oldValue, newValue, filterSet;
            if (this.state.queryValue === null) {
                oldValue = prevState.queryKey;
                newValue = this.state.queryKey;
                filterSet = this.state.commonKeys;
            } else {
                const {queryKey} = this.state;
                oldValue = prevState.queryValue;
                newValue = this.state.queryValue;
                filterSet = this.state.commonValues[queryKey];
                if (!filterSet) {
                    filterSet = [];
                    request("/api/common_values/"+queryKey).then(function (commonValues) {
                        // Save a bit of memory by not saving nonexistent keys
                        if (commonValues.length === 0) return;

                        this.setState((state) => ({
                            commonValues: {
                                ...state.commonValues,
                                [queryKey]: commonValues.map((value) => "" + value),
                            },
                        }));
                    }.bind(this));
                }
            }

            if (!gotNewValues) {
                // Exit if nothing changed
                if (oldValue === newValue) return;
                // Reduce filterSet if possible
                else if (this.state.suggestions !== null && newValue.startsWith(oldValue)) {
                    filterSet = this.state.suggestions;
                }
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
            return true;
        }
    }

    render() {
        const setState = this.setState.bind(this);
        const complete = this.complete.bind(this);
        const {suggestions} = this.state;

        return e("div", {}, [
            e("a", {href: "/item/new"}, "Create new item"),
            e("form", {}, [
                e(AutoComplete, {
                    name: "query",
                    focused: this.state.showSuggestions,
                    value: this.state.query,
                    setValue: function(value) {this.setState(this.setQuery(value));}.bind(this),
                    options: suggestions,
                    index: this.state.suggestionIndex,
                    setIndex(index) {setState({suggestionIndex: index});},
                    complete,
                    onFocus() {setState({showSuggestions: true})},
                    onBlur() {setState({showSuggestions: false})},
                }),
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
