import React from "../react.js";
import ReactDOM from "../react-dom.js";

const e = React.createElement;

class Browser extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            openContainers: {},
        };
        for (const ct in this.props.containers) {
            this.state.openContainers[ct] = false;
        }
        this.state.openContainers[this.props.root] = true;
    }

    renderContainer(ct) {
        const {name, children} = this.props.containers[ct];
        let {open} = this.props;
        if (!open) {
            open = function (ct) {
                window.location = "/browse/container/" + ct;
            }
        }
        return e("table", {className: "browser"}, [
            e("tr", {className: "browser-head"}, [
                e("td", {
                    colSpan: 2,
                    onClick: function () {
                        this.setState((state) => ({
                            openContainers: {
                                ...state.openContainers,
                                [ct]: !state.openContainers[ct],
                            }
                        }));
                    }.bind(this),
                }, e("img", {src: "/static/img/caret_down.svg", className: this.state.openContainers[ct] ? "" : "closed-caret"})),
                e("td", {
                    onClick() {
                        open(ct);
                    },
                }, name),
            ]),
            ...(this.state.openContainers[ct] ? children.map(
                (child) => e("tr", {className: "browser-child"}, [
                    e("td"),
                    e("td"),
                    e("td", {}, this.renderContainer(child))
                ])
            ) : []),
        ]);
    }

    render() {
        return this.renderContainer(this.props.root);
    }
}

ReactDOM.render(React.createElement(Browser, document.props), document.getElementById("root"));
