import React from 'react';
import {Link} from 'react-router-dom';
import {instanceOf} from 'prop-types';
import {withCookies, Cookies} from 'react-cookie';
import './App.css';

// Launch page for the app - button sends to Initial image ratings
class Home extends React.Component {

  static propTypes = {
    cookies: instanceOf(Cookies).isRequired
  };

  constructor(props) {
    super(props);
    const {cookies} = props;
  }

  // React function that is called when the page loads.
  async componentDidMount() {
    const {cookies} = this.props;
    console.log(cookies.get('user'));
    if (cookies.get('user') === undefined) {
      // Send an HTTP request to the server.
      const response = await fetch(
        '/create_user', {method: 'GET'} // The type of HTTP request.
      );
      const data = await response.json()
      cookies.set('user', data.user_id, {path: '/', maxAge: 3600});
    }
  }

  render() {
    return (
      <div className="App">
        <header className="App-header">
          <p>In the following questions, we will try to measure your <br></br>
             preferences over women's tops and dresses.</p>
          <br></br>
          <p>We'll start by showing you a series of random items, and ask <br></br>
             you to rate them from 0 to 10, where 10 is the best. Your rating <br></br>
             should be based on the image: do I like this dress, based on the <br></br>
             photo? Decimals, like 7.5, are fine.</p>
          <br></br>
          <br></br>
          <p>Click the button below to begin.</p>
          <Link className="App-start" to="/initial">Start!</Link>
        </header>
      </div>
    );
  }
}

export default withCookies(Home);
