import React from 'react';
import {Switch, Redirect} from 'react-router-dom';

import {RouteWithLayout} from './components';
import {Main as MainLayout, Minimal as MinimalLayout} from './layouts';

import {
    Import as ImportView,
    Review as ReviewView,
    NotFound as NotFoundView,
    Login as LoginView,
    Home as HomeView,
    Train as TrainView
} from './views';


export const routePermissions = {
    home: ['*'],
    import: ['admin', 'investigator'],
    review: ['admin', 'investigator'],
    train: ['admin', 'researcher']
}


const Routes = () => {
    return (
        <Switch>
            <Redirect
                exact
                from="/"
                to="/home"
            />
            <RouteWithLayout
                component={HomeView}
                exact
                layout={MainLayout}
                useAuth={true}
                permissions={routePermissions['home']}
                path="/home"
            />
            <RouteWithLayout
                component={LoginView}
                exact
                layout={MinimalLayout}
                useAuth={false}
                path="/login"
            />
            <RouteWithLayout
                component={ImportView}
                exact
                layout={MainLayout}
                useAuth={true}
                permissions={routePermissions['import']}
                path="/import"
            />
            <RouteWithLayout
                component={ReviewView}
                exact
                layout={MainLayout}
                useAuth={true}
                permissions={routePermissions['review']}
                path="/review"
            />
            <RouteWithLayout
                component={TrainView}
                exact
                layout={MainLayout}
                useAuth={true}
                permissions={routePermissions['train']}
                path="/train"
            />
            <RouteWithLayout
                component={NotFoundView}
                exact
                layout={MinimalLayout}
                useAuth={false}
                path="/not-found"
            />
            <Redirect to="/not-found"/>
        </Switch>
    );
};

export default Routes;
