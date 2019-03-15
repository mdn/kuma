//@flow
import styled from '@emotion/styled';

export const Row = styled.div`
    display: flex;
    flex-direction: row;
    align-items: center;
`;

export const Spring = styled.div`
    flex: 1 1 0px;
`;

export const Strut = styled.div(props => ({
    flexGrow: 0,
    flexShrink: 0,
    flexBasis: props.width
}));
