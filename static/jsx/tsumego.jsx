var Cell = React.createClass({
    handleClick: function(e) {
        e.preventDefault();
        if (this.props.mode == "remove") {
            this.props.onMove(this.props.coords);
        }
        var classes = this.props.class_name.split(" ")
        if (this.props.mode == "add_opponent") {
            if (classes.indexOf("o_move") != -1) {
                this.props.onMove(this.props.coords);
                return;
            }
        }
        else if (classes.indexOf("move") != -1) {
            this.props.onMove(this.props.coords);
            return;
        }
    },
    render: function() {
        var class_name = "cell " + this.props.class_name;
        return (
            <span className={class_name} onClick={this.handleClick}/>
        );
    }
});

var Row = React.createClass({
    render: function() {
        var cells = this.props.data.map((stone) => (
            <Cell 
                class_name={stone.class_name}
                coords={stone.coords}
                key={stone.coords}
                onMove={this.props.onMove}
                mode={this.props.mode}
            />
        ));

        return (
            <div className="stone-row">
                {cells}
            </div>
        );
    }
});

var Board = React.createClass({
    render: function() {
        var rows = this.props.data.map((row) => (
            <Row
                data={row.stones}
                key={row.id}
                onMove={this.props.onMove}
                mode={this.props.mode}
            />
        ));
        return (
            <div className="board col-md-6">
                {rows}
            </div>
        );
    }
});

var PassButton = React.createClass({
    handleClick: function(e) {
        e.preventDefault();
        this.props.onMove("pass");
    },
    render: function() {
        return <button className="btn btn-default" onClick={this.handleClick}>Pass</button>
    }
});

var LabeledCheckBox = React.createClass({
    render: function() {
        return (
            <div className="checkbox">
                <label>
                    <input type="checkbox" checked={this.props.checked} onChange={this.props.onChange} />
                    {this.props.label}
                </label>
            </div>
        );
    }
});

var RadioGroup = React.createClass({
    render: function() {
        var inputs = this.props.options.map((option) => (
            <div className="radio" key={option}>
                <label>
                    <input
                        type="radio"
                        name={this.props.name}
                        value={option}
                        checked={this.props.selected == option}
                        onChange={this.props.onChange.bind(null, option)}
                    />
                    {option}
                </label>
            </div>
        ));
        return (
            <div>
                {inputs}
            </div>
        );
    }
});

var StatusRow = React.createClass({
    render: function() {
        var data = this.props.data;
        return <p>
            Passes: {data.passes}<br />
            Black captures: {data.black_prisoners}<br />
            White captures: {data.white_prisoners}<br />
            Result: {data.result}
        </p>
    }
});

function handle_status(response) {
    if (response.status >= 200 && response.status < 300) {
        return Promise.resolve(response);
    } else {
        return Promise.reject(new Error(response.statusText));
    }
}

function to_json(response) {
    return response.json();
}

function handle_error(data) {
    if ("error" in data) {
        return Promise.reject(new Error(data.error));
    }
    return Promise.resolve(data);
}

var Game = React.createClass({
    doFetch: function(params) {
        if (!this.state.data.active) {
            console.log("It's over man.");
            return;
        }
        var that = this;
        if (this.state.value) {
            params += "&value=1";
        }
        fetch(window.json_url + "?code=" + escape(this.state.data.code) + params)
        .then(handle_status)
        .then(to_json)
        .then(handle_error)
        .then(
            function(data) {
                console.log(data);
                that.setState({data: data});
            }
        )
        .catch(
            function(error) {
                console.log('Request failed', error);
            }
        );
    },
    handleMove: function(coords) {
        var params = "&" + this.state.mode + "=" + escape(coords);
        if (this.state.vs_book && this.state.mode === "move") {
            params += "&vs_book=1";
        }
        this.doFetch(params);
    },
    handleValueChange: function() {
        // Have to mutate here so that doFetch works correctly.
        this.state.value = !this.state.value;
        this.setState({"value": this.state.value});
        this.doFetch("");
    },
    handleVsBookChange: function() {
        this.setState({"vs_book": !this.state.vs_book});
    },
    handleModeChange: function(mode) {
        this.setState({"mode": mode});
    },
    getInitialState: function() {
        return {
            data: this.props.data,
            "vs_book": true,
            "value": false,
            "mode": "move",
        };
    },
    render: function() {
        var mode_options = ["move", "add_player", "add_opponent", "remove"];
        return (
            <div className="game row">
                <Board data={this.state.data.rows} onMove={this.handleMove} mode={this.state.mode} />
                <div className="col-md-6">
                    <PassButton onMove={this.handleMove} />
                    <LabeledCheckBox label="Show result" checked={this.state.value} onChange={this.handleValueChange} />
                    <LabeledCheckBox label="Play against the book" checked={this.state.vs_book} onChange={this.handleVsBookChange} />
                    <RadioGroup options={mode_options} selected={this.state.mode} onChange={this.handleModeChange} />
                    <StatusRow data={this.state.data} />
                </div>
            </div>
        );
    }
});


ReactDOM.render(
    <Game data={window.state} />,
    document.getElementById('container')
);
