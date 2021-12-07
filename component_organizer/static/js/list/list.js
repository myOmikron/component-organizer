import React from "../react.js";
import ReactDOM from "../react-dom.js";

import {AutoComplete} from "../textinput.js";
import {request} from "../async.js";

const e = React.createElement;

class ItemList extends React.Component {

    constructor(props) {
        super(props);

        const keys = {};
        this.props.queriedKeys.map((key) => {keys[key] = true;});
        this.props.commonKeys.map((key) => {keys[key] = true;});
        this.props.keys.map((key) => {keys[key] = keys[key] | false;});

        let tempQuery = window.location.search.match(/[?&]query=([^&]+)/);
        tempQuery = tempQuery ? decodeURIComponent(tempQuery[1].replace(/\+/g, ' ')) : "";
        this.state = {
            keys,
            query: "",
            queryKey: "",
            queryValue: null, // might be null, when a key is currently entered into query
            queryReplace: [0, 0],
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

        this.queryInput = React.createRef();
    }

    setQuery(query) {
        // index of the character which the cursor is in front of
        const cursor = this.queryInput && this.queryInput.current ? this.queryInput.current.selectionStart : query.length;

        let strippedQuery = query;  // query reduced to the key-value-statement the cursor is in
        let strippedCursor = cursor;  // position of cursor in strippedQuery
        let strippedPosition = [0, query.length];  // position of strippedQuery in original query
        let separator;
        while ((separator = strippedQuery.match(/(?<!\\)[&|()]/d)) !== null) {
            const [start, end] = separator.indices[0];
            if (strippedCursor <= start) {
                strippedQuery = strippedQuery.substring(0, start);
                strippedPosition[1] = strippedPosition[0] + start;
                break;
            /*} else if (strippedCursor < end) {
                console.error("cursor in seperator");  // TODO how to handle this case?
                break;*/
            } else {
                strippedQuery = strippedQuery.substring(end, strippedQuery.length);
                strippedPosition[0] += end;
                strippedCursor -= end;
            }
        }

        let queryKey = strippedQuery.trim();
        let queryValue = null;
        let queryReplace = strippedPosition;

        const comparator = strippedQuery.match(/(?:=|<=|>=|<|>)/d);
        if (comparator) {
            const [start, end] = comparator.indices[0];
            queryKey = strippedQuery.substring(0, start).trim();
            if (strippedCursor <= start) {
                queryReplace = [strippedPosition[0], strippedPosition[0] + start];
            } else if (strippedCursor < end) {
                console.error("cursor in comparator");  // TODO how to handle this case?
            } else {
                queryValue = strippedQuery.substring(end, strippedQuery.length).trim();
                queryReplace = [strippedPosition[0] + end, strippedPosition[1]];
            }
        }
        return {query, queryKey, queryValue, queryReplace};
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
        const {suggestions, suggestionIndex, query, queryReplace} = this.state;
        if (suggestionIndex < 0) return false;

        const newQuery = query.substring(0, queryReplace[0])
                       + suggestions[suggestionIndex]
                       + query.substring(queryReplace[1], query.length);

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

        const shownKeys = this.props.keys.filter((key) => this.state.keys[key]);

        return e("div", {
            className: "flex-vertical",
        }, [
            e("form", {}, [
                e(AutoComplete, {
                    name: "query",
                    className: "searchbar",
                    reference: this.queryInput,
                    focused: this.state.showSuggestions,
                    value: this.state.query,
                    setValue: function(value) {this.setState(this.setQuery.bind(this)(value));}.bind(this),
                    options: suggestions,
                    index: this.state.suggestionIndex,
                    setIndex(index) {setState({suggestionIndex: index});},
                    complete,
                    onFocus() {setState({showSuggestions: true})},
                    onBlur() {setState({showSuggestions: false})},
                }),
                e("input", {type: "submit", value: "Search"})
            ]),
            e("div", {className: "flex-horizontal"}, [
                e("table", {
                    className: "itemtable",
                }, [
                    e("thead", {}, e("tr", {}, [
                        e("th"),
                        ...shownKeys.map((key) => e("th", {}, key)),
                        e("th", {}, "#"),
                    ])),
                    e("tbody", {}, this.props.items.map(({name, url, amount, fields}) => (
                        e("tr", {}, [
                            e("td", {}, e("b", {}, e("a", {href: url}, name))),
                            ...shownKeys.map((key) => e("td", {}, fields[key] || "---")),
                            e("td", {}, amount),
                        ])
                    ))),
                ]),
                e("div", {
                    className: "flex-vertical",
                    style: {alignItems: "start"},
                }, this.props.keys.map((key) => e("div", {
                    style: {cursor: "pointer"},
                    onClick() {
                        setState((state) => ({
                            keys: {
                                ...state.keys,
                                [key]: !state.keys[key],
                            }
                        }));
                    },
                }, [e("span", {
                    style: {color: this.state.keys[key] ? "white" : "gray"},
                }, "\u2022 "), key]))),
            ]),
            e("form", {action: "/item/new"}, e("button", {type: "submit"}, "Create new item")),
        ]);
    }
}

ReactDOM.render(React.createElement(ItemList, document.props), document.getElementById("root"));
