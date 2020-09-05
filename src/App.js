import React from 'react';
import './App.css';
import {
	BrowserRouter as Router,
	Route,
	Switch
} from 'react-router-dom';

// Imports are in order of usage by the application
import Home from "./Home";
import Initial from "./Initial";
import EndInitial from "./EndInitial";
import Refine from "./Refine";
import EndRefine from "./EndRefine";
import Test from "./Test"
import EndTest from "./EndTest"

export default class App extends React.Component {

	render() {
		return (
			<div className="Home">
				<Router>
					<Switch>
            <Route
							exact
							path="/"
							component={Home}
							render={() => (
								<Home />
							)}
						/>
            <Route
							exact
							path="/initial"
							component={Initial}
							render={() => (
								<Initial />
							)}
						/>
            <Route
							exact
							path="/end_initial"
							component={EndInitial}
							render={() => (
								<EndInitial />
							)}
						/>
            <Route
							exact
							path="/refine"
							component={Refine}
							render={() => (
								<Refine />
							)}
						/>
            <Route
							exact
							path="/end_refine"
							component={EndRefine}
							render={() => (
								<EndRefine />
							)}
						/>
			<Route
							exact
							path="/test"
							component={Test}
							render={() => (
								<Test />
							)}
						/>
			<Route
							exact
							path="/end_test"
							component={EndTest}
							render={() => (
								<EndTest />
							)}
						/>
					</Switch>
				</Router>
			</div>
		);
	}
}

