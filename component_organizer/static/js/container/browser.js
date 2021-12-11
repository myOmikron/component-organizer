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
        return e("table", {}, [
            e("tr", {}, [
                e("td", {
                    style: {cursor: "pointer"},
                    onClick: function () {
                        this.setState((state) => ({
                            openContainers: {
                                ...state.openContainers,
                                [ct]: !state.openContainers[ct],
                            }
                        }));
                    }.bind(this),
                }, this.state.openContainers[ct] ? "A" : "V"),
                e("td", {
                    style: {cursor: "pointer"},
                }, name),
            ]),
            ...(this.state.openContainers[ct] ? children.map((child) => e("tr", {}, [e("td"), e("td", {}, this.renderContainer(child))])) : []),
        ]);
    }

    render() {
        return this.renderContainer(this.props.root);
    }
}

ReactDOM.render(React.createElement(Browser, document.props), document.getElementById("root"));
