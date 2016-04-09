var ALPHA = ["A", "B", "C", "D", "E", "F", "G", "H", "J"];

var Cell = React.createClass({
    handleClick: function(e) {
        e.preventDefault();
        if (this.props.mode === "remove") {
            this.props.onMove(this.props.coords);
        }
        if (this.props.mode === "add_opponent") {
            if (this.props.o_move) {
                this.props.onMove(this.props.coords);
                return;
            }
        }
        else if (this.props.move) {
            this.props.onMove(this.props.coords);
            return;
        }
    },
    render: function() {
        var children = [];
        if (this.props.vertical) {
            children.push(<span className={"vertical " + this.props.vertical} key="vertical"/>);
        }
        if (this.props.horizontal) {
            children.push(<span className={"horizontal " + this.props.horizontal} key="horizontal"/>);
        }
        var color;
        switch(this.props.color) {
            case "b":
                color = "black";
                break;
            case "w":
                color = "white";
                break;
            case "k":
                color = "ko";
                break;
            default:
                color = "none";
        }
        var status = "";
        switch(this.props.status) {
            case "t":
                status = "target";
                break;
            case "i":
                status = "immortal";
                break;
            case "e":
                status = "escaped";
                break;
        }
        var color_to_play = this.props.white_to_play ? "white" : "black";
        var opponent_color = this.props.white_to_play ? "black" : "white";
        var class_name = color + " " + status + " cell-content";
        if (this.props.mode === "remove") {
            // pass
        }
        else if (this.props.mode === "add_opponent") {
            if (this.props.o_move) {
                class_name += " " + opponent_color + "-move";
            }
        }
        else {
            if (this.props.move) {
                class_name += " " + color_to_play + "-move";
            }
        }
        children.push(<span className={class_name} key="stone" />);
        if (this.props.last) {
            children.push(<span className="last-move" key="last" />);
        }
        return (
            <div className="cell" onClick={this.handleClick}>
                {children}
            </div>
        );
    }
});

var Row = React.createClass({
    render: function() {
        var {data, ...rest} = this.props;
        var cells = data.map((stone) => (
            <Cell 
                color={stone.c}
                status={stone.s}
                vertical={stone.v}
                horizontal={stone.h}
                move={stone.m}
                o_move={stone.o}
                coords={stone.x}
                key={stone.x}
                last={stone.l}
                {...rest}
            />
        ));
        cells.unshift(<div className="cell alpha number" key="label">{this.props.label}</div>);

        return (
            <div className="stone-row">
                {cells}
            </div>
        );
    }
});

var CoordRow = React.createClass({
    render: function() {
        var cells = [<div className="cell" key="empty" />];
        for (var i = 0; i < this.props.width; i++) {
            cells.push(<div className="cell alpha" key={ALPHA[i]}>{ALPHA[i]}</div>);
        }
        return (
            <div className="stone-row">
                {cells}
            </div>
        );
    }
});

var Board = React.createClass({
    render: function() {
        var {data, width, height, ...rest} = this.props;
        var rows = data.map((row) => (
            <Row
                data={row.stones}
                label={this.props.height - row.index}
                key={row.index}
                {...rest}
            />
        ));
        return (
            <div className="board">
                {rows}
                <CoordRow width={width} />
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

var Button = React.createClass({
    render: function() {
        return <button className="btn btn-default" onClick={this.props.onClick}>{this.props.label}</button>
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
        var inputs = this.props.choices.map((choice) => (
            <div className="radio" key={choice[0]}>
                <label>
                    <input
                        type="radio"
                        name={this.props.name}
                        value={choice[0]}
                        checked={this.props.selected === choice[0]}
                        onChange={this.props.onChange.bind(null, choice[0])}
                    />
                    {choice[1]}
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

var StatsPanel = React.createClass({
    render: function() {
        var data = this.props.data;
        return (
            <p>
                Passes: {data.passes}<br />
                Captures by Black: {data.captures_by_black}<br />
                Captures by White: {data.captures_by_white}<br />
                Result: {data.result}<br />
                Code: <a href={data.tsumego_url}>{data.code}</a>
            </p>
        );
    }
});

var StatusRow = React.createClass({
    render: function() {
        return (
            <p>
                {this.props.status}
            </p>
        );
    }
});

var ChildResults = React.createClass({
    render: function() {
        var that = this;
        var results = this.props.results.map(function(row) {
            var coords = row[0];
            if (coords.length) {
                coords = ALPHA[coords[0]] + (that.props.height - coords[1]);
            }
            else {
                coords = "pass";
            }
            var result = row[1];
            var best = row[2];
            return (<p className={best ? "best-result" : ""} key={coords}>{coords + ": " + result}</p>);
        });
        function cmp(a, b) {
            a = a.key;
            b = b.key;
            if (a < b) {
                return -1;
            }
            else if (a > b) {
                return 1;
            }
            return 0;
        }
        results.sort(cmp);
        return (
            <div>
                {results}
            </div>
        );
    }
});

var NumberInput = React.createClass({
    handleChange: function(e) {
        this.props.onChange(e.target.value);
    },
    render: function() {
        return (
            <div className="form-group">
                <label htmlFor={this.props.label}>{this.props.label}:</label>
                <input
                    id={this.props.label}
                    className="form-control"
                    type="number"
                    value={this.props.value}
                    min={this.props.min}
                    max={this.props.max}
                    onChange={this.handleChange}
                />
            </div>
        );
    }
});

var ProblemForm = React.createClass({
    getInitialState: function() {
        return {"name": "", "collections": []};
    },
    handleNameChange: function(e) {
        this.setState({"name": e.target.value});
    },
    handleCollectionChange: function(e) {
        var options = e.target.options;
        var collections = [];
        // Options is not an Array so no .map
        for (var i = 0; i < options.length; i++) {
            if (options[i].selected) {
                collections.push(options[i].value);
            }
        }
        this.setState({"collections": collections});
    },
    handleSubmit: function(e) {
        e.preventDefault();
        var name = this.state.name.trim();
        var collections = this.state.collections;
        var payload = {
            "action": "add_problem",
            "dump": this.props.dump,
            "name": name,
            "collections": collections
        };
        fetch(window.json_url, {
            method: "post",
            body: JSON.stringify(payload)
        });
    },
    render: function() {
        var options = [
            <option key="a" value="cho">Cho Chikun's encyclopedia of life and death</option>,
            <option key="b" value="gokyo">Gokyo Shumyo</option>
        ];
        return (
            <form onSubmit={this.handleSubmit}>
                <div className="form-group">
                    <label htmlFor="problem_name">Name:</label>
                    <input
                        type="text"
                        className="form-control"
                        id="problem_name"
                        placeholder="Problem name"
                        value={this.state.name}
                        onChange={this.handleNameChange}
                    />
                    <label htmlFor="collections">Collections:</label>
                    <select
                        multiple={true}
                        className="form-control"
                        value={this.state.collections}
                        onChange={this.handleCollectionChange}
                    >
                        {options}
                    </select>
                </div>
                <input type="submit" className="btn btn-default" />
            </form>
        );
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
        if (params.length && !this.state.data.active) {
            console.log("It's over man.");
            return;
        }
        var that = this;
        if (this.state.value) {
            params += "&value=1";
        }
        if (this.state.swap_colors) {
            params += "&color=1";
        }
        if (!this.state.data.active) {
            params += "&dump=" + escape(this.state.data.dump);
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
                console.log("Request failed", error);
            }
        );
    },
    pushUndo: function() {
        if (this.state.data.active) {
            var undos = this.state.undos;
            undos.push(this.state.data.code);
            this.setState({"undos": undos});
        }
    },
    handleUndo: function() {
        var undos = this.state.undos;
        if (undos.length) {
            var code = undos.pop();
            var data = this.state.data;
            var old_code = data.code;
            data.code = code;  // Evil. Can modify props.
            var old_active = data.active;
            data.active = true;
            this.setState({
                "undos": undos,
                "data": data,
            });
            this.doFetch("");
            data.code = old_code;  // Undo the evil.
            data.active = old_active;
        }
    },
    handleMove: function(coords) {
        this.pushUndo();
        var params = "&" + this.state.mode + "=" + escape(coords);
        if (this.state.vs_book && this.state.mode === "move") {
            params += "&vs_book=1";
        }
        this.doFetch(params);
    },
    handleSwap: function() {
        // Have to force update to prevent the UI from blinking as fetch takes a while.
        if (this.state.mode === "add_player") {
            this.setState({"mode": "add_opponent"});
            this.forceUpdate();
        }
        else if (this.state.mode === "add_opponent") {
            this.setState({"mode": "add_player"});
            this.forceUpdate();
        }
        this.doFetch("&swap=1");
    },
    handleBook: function() {
        this.pushUndo();
        var params = "&book=1";
        if (this.state.vs_book) {
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
    handleColorChange: function() {
        // Have to mutate here so that doFetch works correctly.
        this.state.swap_colors = !this.state.swap_colors;
        this.setState({"swap_colors": this.state.swap_colors});
        this.doFetch("");
    },
    handleModeChange: function(mode) {
        this.setState({"mode": mode});
    },
    handleKoThreatsChange: function(value) {
        this.doFetch("&ko_threats=" + value);
    },
    handleReset: function() {
        this.setState({
            "value": false,
            "swap_colors": false,
            "data": this.props.data,
            "undos": []
        });
    },
    getInitialState: function() {
        return {
            "data": this.props.data,
            "vs_book": true,
            "value": false,
            "swap_colors": false,
            "mode": "move",
            "undos": [],
        };
    },
    render: function() {
        var mode_options;
        var mode_labels = ["Move", "Add Black", "Add White", "Remove"];
        if (this.state.data.white_to_play) {
            mode_options = ["move", "add_opponent", "add_player", "remove"];
        }
        else {
            mode_options = ["move", "add_player", "add_opponent", "remove"];
        }
        var mode_choices = [];
        for (var i = 0; i < 4; i++) {
            mode_choices.push([mode_options[i], mode_labels[i]]);
        }
        var child_results = [];
        if (this.state.data.value !== undefined) {
            child_results = this.state.data.value.children;
        }
        return (
            <div className="game row">
                <div className="col-md-5">
                    <Board
                        data={this.state.data.rows}
                        onMove={this.handleMove}
                        mode={this.state.mode}
                        white_to_play={this.state.data.white_to_play}
                        width={this.props.data.width}
                        height={this.props.data.height}
                    />
                    <StatusRow status={this.state.data.status} />
                    <ProblemForm dump={this.state.data.dump} />
                </div>
                <div className="col-md-3">
                    <PassButton onMove={this.handleMove} />
                    <Button label="Undo" onClick={this.handleUndo} />
                    <Button label="Swap" onClick={this.handleSwap} />
                    <Button label="Book" onClick={this.handleBook} />
                    <LabeledCheckBox label="Show result" checked={this.state.value} onChange={this.handleValueChange} />
                    <LabeledCheckBox label="Play against the book" checked={this.state.vs_book} onChange={this.handleVsBookChange} />
                    <LabeledCheckBox label="Swap colors" checked={this.state.swap_colors} onChange={this.handleColorChange} />
                    <NumberInput
                        label="Ko threats"
                        value={this.state.data.ko_threats}
                        min={this.state.data.min_ko_threats}
                        max={this.state.data.max_ko_threats}
                        onChange={this.handleKoThreatsChange}
                    />
                    <RadioGroup choices={mode_choices} selected={this.state.mode} onChange={this.handleModeChange} />
                    <StatsPanel data={this.state.data} />
                    <Button label="Reset" onClick={this.handleReset} />
                </div>
                <div className="col-md-4">
                    <ChildResults results={child_results} height={this.props.data.height} />
                </div>
            </div>
        );
    }
});


ReactDOM.render(
    <Game data={window.state} />,
    document.getElementById("container")
);
