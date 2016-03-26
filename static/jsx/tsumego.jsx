var Cell = React.createClass({
    handleClick: function(e) {
        e.preventDefault();
        if (/move/.test(this.props.class_name)) {
            this.props.onMove(this.props.coords);
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
            <Cell class_name={stone.class_name} coords={stone.coords} key={stone.id} onMove={this.props.onMove}/>
        ));

        return (
            <div className="stone-row">
                {cells}
            </div>
        );
    }
});

var Board = React.createClass({
    handleMove: function(coords) {
        console.log(this.state.data.code);
        console.log(coords);
        var that = this;
        fetch(window.json_url + "?code=" + escape(this.state.data.code) + "&move=" + escape(coords) + "&vs_book=1").then(
            function(response) {
                response.json().then(function(data) {
                    console.log(data);
                    that.setState({data: data});
                });
            }
        );
    },
    getInitialState: function() {
        return {data: this.props.data};
    },
    render: function() {
        var rows = this.state.data.rows.map((row) => (
            <Row data={row.stones} key={row.id} onMove={this.handleMove} />
        ));
        return (
            <div className="board">
                {rows}
            </div>
        );
    }
});


ReactDOM.render(
    <Board data={window.state} />,
    document.getElementById('content')
);
