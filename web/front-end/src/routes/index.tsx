// router component
import {
    BrowserRouter, Routes, Route, Navigate
} from 'react-router-dom';
import HeaderContainerLayout from '@layouts/header-container-layout/header-container-layout';
import Home from '@pages/home/home';
import BeanDetail from '@pages/bean-detail/bean-detail';

const RouterRoot = () => {
    return (
        // react-router-dom v6 123
        // https://reactrouter.com/docs/en/v6/getting-started/overview
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<HeaderContainerLayout />}>
                    <Route
                        index
                        element={<Navigate to="home" replace />}
                    />
                    <Route path="home" element={<Home />} />
                    <Route path="bean-detail" element={<BeanDetail />} />
                </Route>
                <Route
                    path="*"
                    element={(
                        <main>
                            <p>There is nothing here!</p>
                        </main>
                    )}
                />
            </Routes>
        </BrowserRouter>
    );
};

export default RouterRoot;
