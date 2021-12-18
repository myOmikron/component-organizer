import React from "../react.js";
import ReactDOM from "../react-dom.js";

import {ContainerTree, SplitScreen} from "../trees.js";

const e = React.createElement;

class Browser extends React.Component {

    constructor(props) {
        super(props);

        this.state = {
            openContainer: this.props.root,
        };
    }

    render() {
        const setState = this.setState.bind(this);

        return e(SplitScreen, {}, [
            e(ContainerTree, {
                key: "containerTree",
                openContainer(ct) {
                    setState({openContainer: ct});
                },
                createContainer(ct) {
                    window.location = "/container/" + ct + "/new";
                },
                ...this.props
            }),
            null,
            this.state.openContainer,
        ]);
    }
}

ReactDOM.render(e(Browser, document.props), document.getElementById("root"));
