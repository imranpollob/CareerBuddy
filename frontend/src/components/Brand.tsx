/** One vector mark shared by the product, app icons, and browser favicon. */
export function BrandMark({className=''}:{className?:string}){
 return <img className={`brand-symbol ${className}`} src="/brand/careerbuddy-mark.svg" width={32} height={32} alt="" aria-hidden="true" draggable={false}/>
}
export function Brand(){
 return <><BrandMark/><span className="brand-wordmark">CareerBuddy</span></>
}
