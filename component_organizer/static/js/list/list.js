import React from "../react.js";
import ReactDOM from "../react-dom.js";

import TextInput from "../textinput.js";

const e = React.createElement;

class ItemList extends React.Component {

    constructor(props) {
        super(props);

        const tempQuery = window.location.search.match(/[?&]query=([^&]+)/);
        this.state = {
            query: tempQuery ? decodeURIComponent(tempQuery[1].replace(/\+/g, ' ')) : "",
        }
    }

    render() {
        const setState = this.setState.bind(this);

        return e("div", {}, [
            e("a", {href: "/item/new"}, "Create new item"),
            e("form", {}, [
                e("label", {}, e(TextInput, {name: "query", value: this.state.query, setValue(value) {setState({query: value})}})),
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
