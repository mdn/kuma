/*
    Preserving this function so that legacy users don't get errors on their site.
*/
function PromoteMDN() {
	if('console' in window && typeof console.info == 'function') {
		console.info('PromoteMDN is now avaliable for local download at:  https://github.com/riverspirit/promote-mdn-script');
	}
}
